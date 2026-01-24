import { useState, useEffect, useCallback } from 'react';

/**
 * Hook to manage smart bucket filtering for notes
 * Buckets: Inbox, Daily Notes (Phase 5), AI Clusters (Phase 3), Orphans
 */
export const useSmartBuckets = () => {
  const [allNotes, setAllNotes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Bucket states
  const [inboxNotes, setInboxNotes] = useState([]);
  const [dailyNotes, setDailyNotes] = useState([]);
  const [orphanNotes, setOrphanNotes] = useState([]);
  const [aiClusters, setAiClusters] = useState([]);
  const [clustersLoading, setClustersLoading] = useState(false);
  const [clustersError, setClustersError] = useState(null);

  // Fetch all notes from API
  const fetchNotes = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem('token');

      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await fetch('http://localhost:8000/notes/', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          localStorage.removeItem('token');
          localStorage.removeItem('username');
          window.location.reload();
        }
        throw new Error('Failed to fetch notes');
      }

      const data = await response.json();
      setAllNotes(data);

      // Client-side filtering for Inbox
      filterInboxNotes(data);
    } catch (err) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Error fetching notes:', err);
      }
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch daily notes from API
  const fetchDailyNotes = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');

      if (!token) {
        return;
      }

      const response = await fetch('http://localhost:8000/buckets/daily?days=30', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setDailyNotes(data.notes || []);
      } else if (process.env.NODE_ENV === 'development') {
        console.error('Failed to fetch daily notes:', response.status);
      }
    } catch (err) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Error fetching daily notes:', err);
      }
    }
  }, []);

  // Fetch orphaned notes from API
  const fetchOrphanedNotes = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');

      if (!token) {
        return;
      }

      const response = await fetch('http://localhost:8000/buckets/orphans?limit=50', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setOrphanNotes(data.notes || []);
      }
    } catch (err) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Error fetching orphaned notes:', err);
      }
    }
  }, []);

  // Fetch AI clusters from API (Phase 3)
  const fetchAiClusters = useCallback(async (k = 5) => {
    try {
      setClustersLoading(true);
      setClustersError(null);
      const token = localStorage.getItem('token');

      if (!token) {
        return;
      }

      const response = await fetch(`http://localhost:8000/buckets/clusters?k=${k}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        if (response.status === 400) {
          const data = await response.json();
          throw new Error(data.detail || 'Not enough notes for clustering');
        }
        throw new Error('Failed to fetch AI clusters');
      }

      const data = await response.json();
      setAiClusters(data.clusters || []);
    } catch (err) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Error fetching AI clusters:', err);
      }
      setClustersError(err.message);
      setAiClusters([]);
    } finally {
      setClustersLoading(false);
    }
  }, []);

  // Client-side filtering for Inbox bucket
  // Inbox: is_standalone=True, no tags/wikilinks/images, created < 7 days
  const filterInboxNotes = (notes) => {
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

    const inbox = notes.filter(note => {
      // Check if note was created within last 7 days
      const createdAt = new Date(note.created_at);
      const isRecent = createdAt > sevenDaysAgo;

      // Check if standalone (no tags, wikilinks, or images)
      const hasNoTags = !note.tags || note.tags.length === 0;
      const hasNoWikilinks = !note.wikilinks || note.wikilinks.length === 0;
      const hasNoImages = !note.image_id; // Check if note has associated image

      return isRecent && hasNoTags && hasNoWikilinks && hasNoImages;
    });

    setInboxNotes(inbox);
  };

  // Create or open today's daily note
  const createTodayNote = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');

      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await fetch('http://localhost:8000/buckets/daily/today', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to create daily note');
      }

      const data = await response.json();

      // Refresh daily notes list
      await fetchDailyNotes();

      return data;
    } catch (err) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Error creating today\'s note:', err);
      }
      throw err;
    }
  }, [fetchDailyNotes]);

  // Initial load
  useEffect(() => {
    fetchNotes();
    fetchDailyNotes();
    fetchOrphanedNotes();
    fetchAiClusters();
  }, [fetchNotes, fetchDailyNotes, fetchOrphanedNotes, fetchAiClusters]);

  // Refresh function
  const refresh = useCallback(() => {
    fetchNotes();
    fetchDailyNotes();
    fetchOrphanedNotes();
    fetchAiClusters();
  }, [fetchNotes, fetchDailyNotes, fetchOrphanedNotes, fetchAiClusters]);

  return {
    allNotes,
    inboxNotes,
    dailyNotes,
    orphanNotes,
    aiClusters,
    loading,
    error,
    clustersLoading,
    clustersError,
    refresh,
    fetchAiClusters,  // Export to allow manual refresh with different k
    createTodayNote,  // Export to create today's note
  };
};
