/**
 * useBrain - Hook for Brain API operations
 *
 * Provides:
 * - Brain status fetching
 * - Indexing trigger and progress tracking
 * - Training trigger and progress tracking
 * - Adapter management (list, activate)
 */

import { useState, useCallback, useRef, useEffect } from 'react';

const API_BASE = 'http://localhost:8000';

/**
 * Get auth headers for API requests
 */
const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    'Authorization': token ? `Bearer ${token}` : '',
  };
};

/**
 * Hook for Brain functionality
 */
export function useBrain() {
  // Status state
  const [status, setStatus] = useState(null);
  const [adapters, setAdapters] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Operation state
  const [activeOperation, setActiveOperation] = useState(null);
  const pollingRef = useRef(null);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);

  /**
   * Fetch brain status
   */
  const fetchStatus = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/brain/status`, {
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to fetch status: ${response.status}`);
      }

      const data = await response.json();
      setStatus(data);

      // Update operation state based on status
      if (data.status === 'indexing') {
        setActiveOperation({ type: 'indexing', progress: null });
      } else if (data.status === 'training') {
        setActiveOperation({ type: 'training', progress: null });
      } else {
        setActiveOperation(null);
      }

      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Fetch adapters list
   */
  const fetchAdapters = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/brain/adapters`, {
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch adapters');
      }

      const data = await response.json();
      setAdapters(data.adapters || []);
      return data;
    } catch (err) {
      console.error('Failed to fetch adapters:', err);
      return { adapters: [] };
    }
  }, []);

  /**
   * Start brain indexing
   */
  const startIndexing = useCallback(async (fullReindex = false) => {
    setError(null);
    setActiveOperation({ type: 'indexing', progress: 0, step: 'Starting...' });

    try {
      const response = await fetch(
        `${API_BASE}/brain/index?full_reindex=${fullReindex}`,
        {
          method: 'POST',
          headers: getAuthHeaders(),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to start indexing');
      }

      const data = await response.json();

      // Start polling for status
      startPolling();

      return data;
    } catch (err) {
      setError(err.message);
      setActiveOperation(null);
      throw err;
    }
  }, []);

  /**
   * Start brain training
   */
  const startTraining = useCallback(async (config = {}) => {
    setError(null);
    setActiveOperation({ type: 'training', progress: 0, step: 'Initializing...' });

    try {
      const response = await fetch(`${API_BASE}/brain/train`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          base_model: config.baseModel || 'TinyLlama/TinyLlama-1.1B-Chat-v1.0',
          lora_r: config.loraR || 16,
          lora_alpha: config.loraAlpha || 32,
          epochs: config.epochs || 3,
          learning_rate: config.learningRate || 2e-4,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to start training');
      }

      const data = await response.json();

      // Start polling for status
      startPolling();

      return data;
    } catch (err) {
      setError(err.message);
      setActiveOperation(null);
      throw err;
    }
  }, []);

  /**
   * Start polling for operation status
   */
  const startPolling = useCallback(() => {
    // Clear existing polling
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
    }

    // Poll every 3 seconds
    pollingRef.current = setInterval(async () => {
      try {
        const statusData = await fetchStatus();

        // Stop polling if operation completed
        if (statusData.status !== 'indexing' && statusData.status !== 'training') {
          clearInterval(pollingRef.current);
          pollingRef.current = null;
          setActiveOperation(null);

          // Refresh adapters list after training completes
          if (statusData.has_adapter) {
            fetchAdapters();
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 3000);
  }, [fetchStatus, fetchAdapters]);

  /**
   * Activate an adapter version
   */
  const activateAdapter = useCallback(async (version) => {
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE}/brain/adapters/${version}/activate`,
        {
          method: 'POST',
          headers: getAuthHeaders(),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to activate adapter');
      }

      // Refresh status and adapters
      await fetchStatus();
      await fetchAdapters();

      return true;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [fetchStatus, fetchAdapters]);

  /**
   * Delete an adapter version
   */
  const deleteAdapter = useCallback(async (version) => {
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE}/brain/adapters/${version}`,
        {
          method: 'DELETE',
          headers: getAuthHeaders(),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to delete adapter');
      }

      // Refresh adapters list
      await fetchAdapters();

      return true;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [fetchAdapters]);

  /**
   * Format timestamp for display
   */
  const formatDate = useCallback((dateString) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleDateString([], {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  }, []);

  return {
    // Status data
    status,
    adapters,
    isLoading,
    error,
    activeOperation,

    // Computed values
    hasAdapter: status?.has_adapter || false,
    activeVersion: status?.active_version || null,
    brainStatus: status?.status || 'none',
    notesIndexed: status?.notes_indexed || 0,
    imagesIndexed: status?.images_indexed || 0,
    samplesCount: status?.samples_count || 0,
    factsCount: status?.facts_count || 0,
    lastIndexed: status?.last_indexed,
    lastTrained: status?.last_trained,

    // Operations
    fetchStatus,
    fetchAdapters,
    startIndexing,
    startTraining,
    activateAdapter,
    deleteAdapter,

    // Utilities
    formatDate,

    // Derived states
    isIndexing: activeOperation?.type === 'indexing',
    isTraining: activeOperation?.type === 'training',
    canTrain: (status?.samples_count || 0) > 0 && !activeOperation,
    canIndex: !activeOperation,
  };
}

export default useBrain;
