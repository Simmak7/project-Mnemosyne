/**
 * Hook for model pull (SSE), delete, update checking, and state tracking.
 * Uses api.fetch for CSRF + auth handling.
 */
import { useState, useCallback, useRef } from 'react';
import { api } from '../../../utils/api';

export function useModelManagement(onModelsChanged) {
  // Map of modelId -> { status, percent, error }
  const [pullProgress, setPullProgress] = useState({});
  // Map of modelName -> { update_available, status, local_digest, remote_digest }
  const [updateStatus, setUpdateStatus] = useState({});
  const [checkingUpdates, setCheckingUpdates] = useState(false);
  const abortRefs = useRef({});

  const pullModel = useCallback(async (modelName) => {
    setPullProgress(prev => ({
      ...prev,
      [modelName]: { status: 'connecting', percent: 0, error: null },
    }));

    const controller = new AbortController();
    abortRefs.current[modelName] = controller;

    try {
      const response = await api.fetch('/models/pull', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: modelName }),
        signal: controller.signal,
      });

      if (!response.ok) {
        setPullProgress(prev => ({
          ...prev,
          [modelName]: { status: 'error', percent: 0, error: `HTTP ${response.status}` },
        }));
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      const processLine = (line) => {
        if (!line.startsWith('data: ')) return;
        try {
          const data = JSON.parse(line.slice(6));
          setPullProgress(prev => ({
            ...prev,
            [modelName]: {
              status: data.status || 'downloading',
              percent: data.percent || 0,
              error: data.error || null,
            },
          }));

          if (data.status === 'success') {
            // Clear update status for this model after successful pull
            setUpdateStatus(prev => {
              const next = { ...prev };
              delete next[modelName];
              return next;
            });
            if (onModelsChanged) onModelsChanged();
          }
        } catch {
          // skip malformed JSON
        }
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          processLine(line);
        }
      }

      // Process any remaining data in buffer after stream ends
      if (buffer.trim()) {
        processLine(buffer.trim());
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setPullProgress(prev => ({
          ...prev,
          [modelName]: { status: 'error', percent: 0, error: err.message },
        }));
      }
    } finally {
      delete abortRefs.current[modelName];
    }
  }, [onModelsChanged]);

  const cancelPull = useCallback((modelName) => {
    if (abortRefs.current[modelName]) {
      abortRefs.current[modelName].abort();
      setPullProgress(prev => {
        const next = { ...prev };
        delete next[modelName];
        return next;
      });
    }
  }, []);

  const deleteModel = useCallback(async (modelName) => {
    try {
      const response = await api.fetch(`/models/${encodeURIComponent(modelName)}`, {
        method: 'DELETE',
      });
      const data = await response.json();
      if (data.status === 'success' && onModelsChanged) {
        onModelsChanged();
      }
      return data;
    } catch (err) {
      return { status: 'error', error: err.message };
    }
  }, [onModelsChanged]);

  const clearProgress = useCallback((modelName) => {
    setPullProgress(prev => {
      const next = { ...prev };
      delete next[modelName];
      return next;
    });
  }, []);

  const checkForUpdates = useCallback(async (force = false) => {
    setCheckingUpdates(true);
    try {
      const resp = await api.fetch(`/models/updates?force=${force}`);
      if (resp.ok) {
        const data = await resp.json();
        const statusMap = {};
        for (const u of data.updates || []) {
          statusMap[u.model] = u;
        }
        setUpdateStatus(statusMap);
      }
    } catch (err) {
      console.error('Failed to check for updates:', err);
    } finally {
      setCheckingUpdates(false);
    }
  }, []);

  return {
    pullProgress, pullModel, cancelPull, deleteModel, clearProgress,
    updateStatus, checkingUpdates, checkForUpdates,
  };
}

export default useModelManagement;
