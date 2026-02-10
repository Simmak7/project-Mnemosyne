import React, { createContext, useContext, useState, useCallback, useEffect, useLayoutEffect, useRef } from 'react';
import { api } from '../../../utils/api';
import { usePersistedState } from '../../../hooks/usePersistedState';

/**
 * NoteContext - State management for the Notes feature
 * Manages categories, selection, filtering, and note data
 */
const NoteContext = createContext(null);

export function NoteProvider({ children, initialNoteId = null }) {
  // Persisted state - survives tab switches and page reloads
  const [currentCategory, setCurrentCategory] = usePersistedState('notes:category', 'all');
  const [selectedNoteId, setSelectedNoteId] = usePersistedState('notes:selectedId', null);
  const [selectedCollectionId, setSelectedCollectionId] = usePersistedState('notes:collectionId', null);
  const [sortBy, setSortBy] = usePersistedState('notes:sortBy', 'updated');
  const [sortOrder, setSortOrder] = usePersistedState('notes:sortOrder', 'desc');
  const [viewMode, setViewMode] = usePersistedState('notes:viewMode', 'list');

  // Ephemeral state - resets on remount (intentional)
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTagFilter, setSelectedTagFilter] = useState(null);

  // Data state (will be populated by API calls in Phase 2)
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Category counts (will be fetched from API)
  const [categoryCounts, setCategoryCounts] = useState({
    all: 0,
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

  // Skip one validation cycle after external navigation to prevent race condition
  const [skipValidation, setSkipValidation] = useState(false);

  // Sync selectedNoteId when initialNoteId changes (external navigation from Brain Graph, Journal, etc.)
  // useLayoutEffect ensures it fires BEFORE child components render with stale value
  // Ref starts at null so the FIRST mount with a non-null ID always triggers
  const prevInitialId = useRef(null);
  useLayoutEffect(() => {
    if (initialNoteId != null && initialNoteId !== prevInitialId.current) {
      setSelectedNoteId(initialNoteId);
      // Reset to 'all' so the note is always visible regardless of previous category filter
      setCurrentCategory('all');
      // Skip next validation cycle so useValidateNoteSelection doesn't clear the selection
      // before the note list has a chance to include the target note
      setSkipValidation(true);
    }
    prevInitialId.current = initialNoteId;
  }, [initialNoteId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Fetch category counts on mount
  useEffect(() => {
    fetchCategoryCounts();
    fetchSmartTags();
  }, []);

  const fetchCategoryCounts = useCallback(async () => {
    try {
      // Use /notes-enhanced/ to get image_ids, is_standalone, is_reviewed fields
      const [allNotes, trashedNotes] = await Promise.all([
        api.get('/notes-enhanced/'),
        api.get('/notes/trash/').catch(() => [])
      ]);

      const counts = {
        all: allNotes.length,
        inbox: allNotes.filter(n => isRecentNote(n)).length,
        smart: allNotes.filter(n =>
          (n.image_ids && n.image_ids.length > 0) || n.is_standalone === false
        ).length,
        manual: allNotes.filter(n =>
          (!n.image_ids || n.image_ids.length === 0) && n.is_standalone !== false
        ).length,
        daily: allNotes.filter(n => isDailyNote(n)).length,
        favorites: allNotes.filter(n => n.is_favorite).length,
        review: allNotes.filter(n =>
          (n.image_ids && n.image_ids.length > 0) && !n.is_reviewed
        ).length,
        trash: trashedNotes.length
      };

      setCategoryCounts(counts);
    } catch (error) {
      console.error('Error fetching category counts:', error);
    }
  }, []);

  const fetchSmartTags = useCallback(async () => {
    try {
      const tags = await api.get('/tags/');
      const smartTagsList = tags
        .filter(tag => tag.note_count > 0)
        .sort((a, b) => (b.note_count || 0) - (a.note_count || 0))
        .slice(0, 10)
        .map(tag => ({
          name: tag.name,
          count: tag.note_count || 0
        }));

      setSmartTags(smartTagsList);
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
           note.title?.match(/^\d{4}-\d{2}-\d{2}/) ||
           note.title?.toLowerCase().includes('journal');
  };

  // Flag to auto-open editor after selecting a newly created note
  const [editAfterSelect, setEditAfterSelect] = useState(false);

  // Actions
  const selectNote = useCallback((noteId) => {
    setSelectedNoteId(noteId);
  }, []);

  const selectNoteForEditing = useCallback((noteId) => {
    setEditAfterSelect(true);
    setSelectedNoteId(noteId);
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedNoteId(null);
    setEditAfterSelect(false);
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
    selectNoteForEditing,
    clearSelection,
    editAfterSelect,
    setEditAfterSelect,

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

    // Validation skip (for external navigation)
    skipValidation,
    setSkipValidation,

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
