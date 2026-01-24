import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';

/**
 * NoteContext - State management for the Notes feature
 * Manages categories, selection, filtering, and note data
 */
const NoteContext = createContext(null);

export function NoteProvider({ children, initialNoteId = null }) {
  // Category state
  const [currentCategory, setCurrentCategory] = useState('inbox');

  // Note selection state
  const [selectedNoteId, setSelectedNoteId] = useState(initialNoteId);

  // Collection state
  const [selectedCollectionId, setSelectedCollectionId] = useState(null);

  // Search and filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTagFilter, setSelectedTagFilter] = useState(null);
  const [sortBy, setSortBy] = useState('updated'); // 'updated' | 'created' | 'title'
  const [sortOrder, setSortOrder] = useState('desc');
  const [viewMode, setViewMode] = useState('list'); // 'list' | 'grid'

  // Data state (will be populated by API calls in Phase 2)
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Category counts (will be fetched from API)
  const [categoryCounts, setCategoryCounts] = useState({
    inbox: 0,
    smart: 0,
    manual: 0,
    daily: 0,
    favorites: 0,
    review: 0,
    trash: 0
  });

  // Smart tags (popular tags auto-extracted)
  const [smartTags, setSmartTags] = useState([]);

  // Update selectedNoteId when initialNoteId changes (from external navigation)
  useEffect(() => {
    if (initialNoteId !== null) {
      setSelectedNoteId(initialNoteId);
    }
  }, [initialNoteId]);

  // Fetch category counts on mount
  useEffect(() => {
    fetchCategoryCounts();
    fetchSmartTags();
  }, []);

  const fetchCategoryCounts = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      // Fetch notes and trash to calculate counts
      const [notesResponse, trashResponse] = await Promise.all([
        fetch('http://localhost:8000/notes/', {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch('http://localhost:8000/notes/trash/', {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      if (notesResponse.ok) {
        const allNotes = await notesResponse.json();
        const trashedNotes = trashResponse.ok ? await trashResponse.json() : [];

        // Calculate counts based on note properties
        const counts = {
          inbox: allNotes.filter(n => isRecentNote(n)).length,
          smart: allNotes.filter(n => n.source_type === 'image' || n.source_type === 'ai').length,
          manual: allNotes.filter(n => !n.source_type || n.source_type === 'manual').length,
          daily: allNotes.filter(n => isDailyNote(n)).length,
          favorites: allNotes.filter(n => n.is_favorite).length,
          review: allNotes.filter(n => needsReview(n)).length,
          trash: trashedNotes.length
        };

        setCategoryCounts(counts);
      }
    } catch (error) {
      console.error('Error fetching category counts:', error);
    }
  }, []);

  const fetchSmartTags = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await fetch('http://localhost:8000/tags/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const tags = await response.json();
        // Transform to smart tags format with counts
        const smartTagsList = tags
          .filter(tag => tag.note_count > 0)
          .sort((a, b) => (b.note_count || 0) - (a.note_count || 0))
          .slice(0, 10) // Top 10 tags
          .map(tag => ({
            name: tag.name,
            count: tag.note_count || 0
          }));

        setSmartTags(smartTagsList);
      }
    } catch (error) {
      console.error('Error fetching smart tags:', error);
    }
  }, []);

  // Helper functions for categorization
  const isRecentNote = (note) => {
    if (!note.created_at) return false;
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
    return new Date(note.created_at) > sevenDaysAgo;
  };

  const isDailyNote = (note) => {
    return note.title?.startsWith('Daily Note') ||
           note.title?.match(/^\d{4}-\d{2}-\d{2}$/) ||
           note.source_type === 'daily';
  };

  const needsReview = (note) => {
    // AI-generated notes that haven't been reviewed
    const isAIGenerated = note.source_type === 'image' || note.source_type === 'ai';
    const notReviewed = !note.is_reviewed;
    return isAIGenerated && notReviewed;
  };

  // Actions
  const selectNote = useCallback((noteId) => {
    setSelectedNoteId(noteId);
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedNoteId(null);
  }, []);

  const refreshCounts = useCallback(() => {
    fetchCategoryCounts();
    fetchSmartTags();
  }, [fetchCategoryCounts, fetchSmartTags]);

  const value = {
    // Category state
    currentCategory,
    setCurrentCategory,
    categoryCounts,

    // Note selection
    selectedNoteId,
    selectNote,
    clearSelection,

    // Collection selection
    selectedCollectionId,
    setSelectedCollectionId,

    // Search and filter
    searchQuery,
    setSearchQuery,
    selectedTagFilter,
    setSelectedTagFilter,
    sortBy,
    setSortBy,
    sortOrder,
    setSortOrder,
    viewMode,
    setViewMode,

    // Data
    notes,
    setNotes,
    loading,
    setLoading,
    error,
    setError,

    // Smart tags
    smartTags,

    // Actions
    refreshCounts
  };

  return (
    <NoteContext.Provider value={value}>
      {children}
    </NoteContext.Provider>
  );
}

export function useNoteContext() {
  const context = useContext(NoteContext);
  if (!context) {
    throw new Error('useNoteContext must be used within a NoteProvider');
  }
  return context;
}

export default NoteContext;
