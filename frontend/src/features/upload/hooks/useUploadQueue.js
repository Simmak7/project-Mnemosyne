/**
 * useUploadQueue Hook
 * Manages the multi-file upload queue with status tracking
 */

import { useState, useCallback, useRef } from 'react';
import { api } from '../../../utils/api';
import { validateFile } from '../utils/fileValidation';
import { composePrompt } from '../utils/promptComposer';
import { getModelId } from '../utils/modelMapper';

// File states
export const FILE_STATES = {
  PENDING: 'pending',
  UPLOADING: 'uploading',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed'
};

/**
 * Generate unique ID for queued files
 */
let fileIdCounter = 0;
function generateFileId() {
  return `file_${Date.now()}_${++fileIdCounter}`;
}

/**
 * Upload queue hook
 * @param {object} options - Hook options
 * @param {function} options.onUploadSuccess - Callback when file completes
 * @param {function} options.onUploadError - Callback when file fails
 * @returns {object} - Queue state and actions
 */
export function useUploadQueue({ onUploadSuccess, onUploadError } = {}) {
  // Queue state: Array of file objects with metadata
  const [files, setFiles] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);

  // Ref to track current processing state for async operations
  const processingRef = useRef(false);
  const abortControllerRef = useRef(null);

  /**
   * Add files to the queue
   * @param {FileList|File[]} newFiles - Files to add
   * @returns {{ added: number, rejected: Array }} - Result summary
   */
  const addFiles = useCallback((newFiles) => {
    const added = [];
    const rejected = [];

    Array.from(newFiles).forEach(file => {
      const validation = validateFile(file);

      if (validation.valid) {
        added.push({
          id: generateFileId(),
          file,
          name: file.name,
          size: file.size,
          type: file.type,
          status: FILE_STATES.PENDING,
          progress: 0,
          error: null,
          result: null,
          taskId: null,
          // Per-file config (advanced feature, uses batch config by default)
          customPrompt: null,
          useCustomPrompt: false
        });
      } else {
        rejected.push({ file, error: validation.error });
      }
    });

    if (added.length > 0) {
      setFiles(prev => [...prev, ...added]);
    }

    return { added: added.length, rejected };
  }, []);

  /**
   * Remove a file from the queue
   * @param {string} fileId - ID of file to remove
   */
  const removeFile = useCallback((fileId) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  }, []);

  /**
   * Clear all completed files from queue
   */
  const clearCompleted = useCallback(() => {
    setFiles(prev => prev.filter(f => f.status !== FILE_STATES.COMPLETED));
  }, []);

  /**
   * Clear all files from queue
   */
  const clearAll = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setFiles([]);
    setIsProcessing(false);
    processingRef.current = false;
  }, []);

  /**
   * Update a specific file's state
   */
  const updateFile = useCallback((fileId, updates) => {
    setFiles(prev => prev.map(f =>
      f.id === fileId ? { ...f, ...updates } : f
    ));
  }, []);

  /**
   * Upload a single file to the server
   */
  const uploadSingleFile = useCallback(async (queuedFile, config, signal) => {
    const { file, id } = queuedFile;
    const isDocument = file.type === 'application/pdf';

    // Update status to uploading
    updateFile(id, { status: FILE_STATES.UPLOADING, progress: 0 });

    try {
      // Create form data
      const formData = new FormData();
      formData.append('file', file);

      let uploadEndpoint, statusEndpoint;

      if (isDocument) {
        // Route PDFs to the documents endpoint
        uploadEndpoint = '/documents/upload/';
        statusEndpoint = '/documents/task-status/';

        // Send user instructions for PDF analysis if provided
        const instructions = queuedFile.useCustomPrompt
          ? queuedFile.customPrompt
          : config.userPrompt;
        if (instructions) formData.append('instructions', instructions);
      } else {
        // Route images to the existing image endpoint
        uploadEndpoint = '/upload-image/';
        statusEndpoint = '/task-status/';

        // Compose prompt (null = use backend default)
        const prompt = composePrompt({
          userPrompt: queuedFile.useCustomPrompt ? queuedFile.customPrompt : config.userPrompt,
          preset: config.preset,
          depth: config.analysisDepth
        });

        if (prompt) formData.append('prompt', prompt);
        if (config.targetAlbumId) formData.append('album_id', config.targetAlbumId);
        if (config.autoTagging !== undefined) formData.append('auto_tagging', config.autoTagging);
        if (config.maxTags !== undefined) formData.append('max_tags', config.maxTags);
        if (config.autoCreateNote !== undefined) formData.append('auto_create_note', config.autoCreateNote);
      }

      // Upload file using centralized API (handles cookies, CSRF, token refresh)
      const response = await api.fetch(uploadEndpoint, {
        method: 'POST',
        body: formData,
        signal
      });

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          throw new Error('Session expired. Please login again.');
        }
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data = await response.json();

      // Update to processing state
      updateFile(id, {
        status: FILE_STATES.PROCESSING,
        progress: 50,
        taskId: data.task_id,
        imageId: data.image_id,
        documentId: data.document_id,
        isDocument,
        statusEndpoint,
      });

      // Poll for completion
      await pollTaskStatus(id, data.task_id, signal, statusEndpoint);

      return data;

    } catch (error) {
      if (error.name === 'AbortError') {
        updateFile(id, { status: FILE_STATES.PENDING, progress: 0 });
        throw error;
      }

      updateFile(id, {
        status: FILE_STATES.FAILED,
        error: error.message,
        progress: 0
      });

      onUploadError?.(queuedFile, error);
      throw error;
    }
  }, [updateFile, onUploadError]);

  /**
   * Poll task status until completion
   * Extended timeout (5 minutes) for AI analysis which can take 2-3+ minutes
   */
  const pollTaskStatus = useCallback(async (fileId, taskId, signal, statusEndpoint = '/task-status/') => {
    const maxAttempts = 300; // 5 minutes with 1s interval (AI can be slow)
    const slowWarningThreshold = 120; // Show "slow" indicator after 2 minutes
    let attempts = 0;

    while (attempts < maxAttempts) {
      if (signal?.aborted) {
        throw new DOMException('Aborted', 'AbortError');
      }

      try {
        const response = await api.fetch(`${statusEndpoint}${taskId}`, { signal });

        if (!response.ok) {
          throw new Error('Failed to check task status');
        }

        const status = await response.json();

        // Update progress based on status
        if (status.status === 'SUCCESS') {
          updateFile(fileId, {
            status: FILE_STATES.COMPLETED,
            progress: 100,
            result: status.result
          });

          // Call success callback after state update
          onUploadSuccess?.({ id: fileId }, status.result);

          return status;
        }

        if (status.status === 'FAILURE') {
          throw new Error(status.error || 'Analysis failed');
        }

        // Still processing, update progress estimation
        // Progress: 50-75% in first 90s, 75-95% after that
        let progressEstimate;
        if (attempts < slowWarningThreshold) {
          progressEstimate = Math.min(50 + (attempts * 0.28), 75);
        } else {
          progressEstimate = Math.min(75 + ((attempts - slowWarningThreshold) * 0.22), 95);
        }

        // Add slow indicator if taking longer than expected
        const isSlow = attempts >= slowWarningThreshold;
        updateFile(fileId, {
          progress: progressEstimate,
          isSlow: isSlow
        });

      } catch (error) {
        if (error.name === 'AbortError') throw error;
        // Ignore polling errors and retry
      }

      // Wait 1 second before next poll
      await new Promise(resolve => setTimeout(resolve, 1000));
      attempts++;
    }

    // Timeout after 5 minutes - but check if image was actually processed in the background
    throw new Error('AI analysis timed out after 5 minutes. The image may still be processing - check the Gallery shortly.');
  }, [updateFile, onUploadSuccess]);

  /**
   * Process all pending files in queue
   * @param {object} config - Analysis configuration
   */
  const processQueue = useCallback(async (config = {}) => {
    if (processingRef.current) return;

    const pendingFiles = files.filter(f => f.status === FILE_STATES.PENDING);
    if (pendingFiles.length === 0) return;

    processingRef.current = true;
    setIsProcessing(true);
    abortControllerRef.current = new AbortController();

    try {
      // Process files sequentially to avoid overwhelming the server
      for (const queuedFile of pendingFiles) {
        if (!processingRef.current) break;

        try {
          await uploadSingleFile(queuedFile, config, abortControllerRef.current.signal);
        } catch (error) {
          if (error.name === 'AbortError') break;
          // Continue with next file on error
          console.error(`Failed to process ${queuedFile.name}:`, error);
        }
      }
    } finally {
      processingRef.current = false;
      setIsProcessing(false);
      abortControllerRef.current = null;
    }
  }, [files, uploadSingleFile]);

  /**
   * Stop processing
   */
  const stopProcessing = useCallback(() => {
    processingRef.current = false;
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  /**
   * Retry a failed file
   * @param {string} fileId - ID of file to retry
   */
  const retryFile = useCallback((fileId) => {
    updateFile(fileId, {
      status: FILE_STATES.PENDING,
      error: null,
      progress: 0
    });
  }, [updateFile]);

  /**
   * Set custom prompt for a specific file
   */
  const setFileCustomPrompt = useCallback((fileId, prompt, useCustom = true) => {
    updateFile(fileId, {
      customPrompt: prompt,
      useCustomPrompt: useCustom
    });
  }, [updateFile]);

  // Computed values
  const pendingCount = files.filter(f => f.status === FILE_STATES.PENDING).length;
  const completedCount = files.filter(f => f.status === FILE_STATES.COMPLETED).length;
  const failedCount = files.filter(f => f.status === FILE_STATES.FAILED).length;
  const totalCount = files.length;

  return {
    // State
    files,
    isProcessing,
    pendingCount,
    completedCount,
    failedCount,
    totalCount,

    // Actions
    addFiles,
    removeFile,
    clearCompleted,
    clearAll,
    processQueue,
    stopProcessing,
    retryFile,
    setFileCustomPrompt
  };
}

export default useUploadQueue;
