/**
 * useMnemosyneBrain - Hook for Mnemosyne Brain management operations.
 *
 * Handles brain build, status, and file management (separate from chat).
 */

import { useState, useCallback, useRef } from 'react';

const API_BASE = 'http://localhost:8000';

const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    'Authorization': token ? `Bearer ${token}` : '',
  };
};

export function useMnemosyneBrain() {
  const [brainStatus, setBrainStatus] = useState(null);
  const [buildStatus, setBuildStatus] = useState(null);
  const [brainFiles, setBrainFiles] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const pollRef = useRef(null);

  // Fetch overall brain status
  const fetchBrainStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/mnemosyne/status`, {
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        const data = await response.json();
        setBrainStatus(data);
        return data;
      }
    } catch (err) {
      console.error('Failed to fetch brain status:', err);
    }
    return null;
  }, []);

  // Trigger brain build
  const triggerBuild = useCallback(async (fullRebuild = true) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/mnemosyne/build`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ full_rebuild: fullRebuild }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || 'Build failed');
      }

      const data = await response.json();
      setBuildStatus(data);

      // Start polling for progress
      startBuildPolling();

      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Fetch build status
  const fetchBuildStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/mnemosyne/build/status`, {
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        const data = await response.json();
        setBuildStatus(data);
        return data;
      }
    } catch (err) {
      console.error('Failed to fetch build status:', err);
    }
    return null;
  }, []);

  // Poll build status until complete
  const startBuildPolling = useCallback(() => {
    if (pollRef.current) clearInterval(pollRef.current);

    pollRef.current = setInterval(async () => {
      const status = await fetchBuildStatus();
      if (status && (status.status === 'completed' || status.status === 'failed' || status.status === 'none')) {
        clearInterval(pollRef.current);
        pollRef.current = null;
        // Refresh brain status after build completes
        fetchBrainStatus();
      }
    }, 3000);
  }, [fetchBuildStatus, fetchBrainStatus]);

  // Stop polling
  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  // Fetch brain files list
  const fetchBrainFiles = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/mnemosyne/files`, {
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        const data = await response.json();
        setBrainFiles(data);
        return data;
      }
    } catch (err) {
      console.error('Failed to fetch brain files:', err);
    }
    return [];
  }, []);

  // Fetch single brain file
  const fetchBrainFile = useCallback(async (fileKey) => {
    try {
      const response = await fetch(`${API_BASE}/mnemosyne/files/${fileKey}`, {
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        return await response.json();
      }
    } catch (err) {
      console.error('Failed to fetch brain file:', err);
    }
    return null;
  }, []);

  // Update brain file content
  const updateBrainFile = useCallback(async (fileKey, content) => {
    try {
      const response = await fetch(`${API_BASE}/mnemosyne/files/${fileKey}`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify({ content }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || 'Update failed');
      }

      return await response.json();
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  return {
    // State
    brainStatus,
    buildStatus,
    brainFiles,
    isLoading,
    error,

    // Status
    hasBrain: brainStatus?.has_brain || false,
    isReady: brainStatus?.is_ready || false,
    isBuilding: brainStatus?.is_building || buildStatus?.status === 'running',
    isStale: brainStatus?.is_stale || false,

    // Actions
    fetchBrainStatus,
    triggerBuild,
    fetchBuildStatus,
    startBuildPolling,
    stopPolling,
    fetchBrainFiles,
    fetchBrainFile,
    updateBrainFile,
  };
}

export default useMnemosyneBrain;
