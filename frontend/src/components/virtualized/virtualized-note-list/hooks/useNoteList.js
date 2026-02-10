/**
 * useNoteList - Data fetching and state management for note list
 */
import { useState, useCallback, useEffect } from 'react';

export function useNoteList() {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  const fetchNotes = useCallback(async (pageNum) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        console.error('No token found');
        return [];
      }

      const response = await fetch(
        `http://localhost:8000/notes/?skip=${(pageNum - 1) * 50}&limit=50`,
        {
          headers: { 'Authorization': `Bearer ${token}` },
        }
      );

      if (response.ok) {
        return await response.json();
      } else if (response.status === 401 || response.status === 403) {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        window.location.reload();
      }
      return [];
    } catch (error) {
      console.error('Error fetching notes:', error);
      return [];
    }
  }, []);

  // Initial load
  useEffect(() => {
    const loadInitialNotes = async () => {
      setLoading(true);
      const initialNotes = await fetchNotes(1);
      setNotes(initialNotes);
      setHasMore(initialNotes.length === 50);
      setLoading(false);
    };
    loadInitialNotes();
  }, [fetchNotes]);

  const loadMore = useCallback(async () => {
    if (loading || !hasMore) return;

    setLoading(true);
    const nextPage = page + 1;
    const newNotes = await fetchNotes(nextPage);

    if (newNotes.length === 0) {
      setHasMore(false);
    } else {
      setNotes(prev => [...prev, ...newNotes]);
      setPage(nextPage);
      setHasMore(newNotes.length === 50);
    }
    setLoading(false);
  }, [fetchNotes, page, loading, hasMore]);

  const addNote = useCallback((note) => {
    setNotes(prev => [note, ...prev]);
  }, []);

  const updateNote = useCallback((updatedNote) => {
    setNotes(prev =>
      prev.map(note => (note.id === updatedNote.id ? updatedNote : note))
    );
  }, []);

  const removeNote = useCallback((noteId) => {
    setNotes(prev => prev.filter(note => note.id !== noteId));
  }, []);

  return {
    notes,
    loading,
    hasMore,
    loadMore,
    addNote,
    updateNote,
    removeNote,
  };
}

export default useNoteList;
