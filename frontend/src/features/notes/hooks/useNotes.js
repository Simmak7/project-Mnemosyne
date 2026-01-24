import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback, useMemo } from 'react';
import { useNoteContext } from './NoteContext';

const API_BASE = 'http://localhost:8000';

/**
 * useNotes - Hook for fetching and filtering notes
 * Integrates with NoteContext for category/filter state
 */
export function useNotes() {
  const {
    currentCategory,
    searchQuery,
    selectedTagFilter,
    selectedCollectionId,
    sortBy,
    sortOrder
  } = useNoteContext();

  const queryClient = useQueryClient();

  // Base query for all notes (enhanced with relationships)
  const {
    data: rawNotes = [],
    isLoading: isLoadingNotes,
    isError: isErrorNotes,
    error: errorNotes,
    refetch: refetchNotes
  } = useQuery({
    queryKey: ['notes-enhanced'],
    queryFn: async () => {
      const token = localStorage.getItem('token');
      if (!token) throw new Error('Not authenticated');

      const response = await fetch(`${API_BASE}/notes-enhanced/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          localStorage.removeItem('token');
          localStorage.removeItem('username');
          window.location.reload();
        }
        throw new Error('Failed to fetch notes');
      }

      return response.json();
    },
    staleTime: 30000,
    refetchOnWindowFocus: false
  });

  // Query for trashed notes (only when trash category is selected)
  const {
    data: trashedNotes = [],
    isLoading: isLoadingTrash,
    isError: isErrorTrash,
    error: errorTrash,
    refetch: refetchTrash
  } = useQuery({
    queryKey: ['notes-trash'],
    queryFn: async () => {
      const token = localStorage.getItem('token');
      if (!token) throw new Error('Not authenticated');

      const response = await fetch(`${API_BASE}/notes/trash/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Failed to fetch trashed notes');
      return response.json();
    },
    enabled: currentCategory === 'trash',
    staleTime: 30000,
    refetchOnWindowFocus: false
  });

  // Query for collection notes (only when collection category is selected)
  const {
    data: collectionData = null,
    isLoading: isLoadingCollection,
    isError: isErrorCollection,
    error: errorCollection,
    refetch: refetchCollection
  } = useQuery({
    queryKey: ['collection', selectedCollectionId],
    queryFn: async () => {
      const token = localStorage.getItem('token');
      if (!token) throw new Error('Not authenticated');

      const response = await fetch(`${API_BASE}/collections/${selectedCollectionId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Failed to fetch collection');
      return response.json();
    },
    enabled: currentCategory === 'collection' && !!selectedCollectionId,
    staleTime: 30000,
    refetchOnWindowFocus: false
  });

  // Combined loading/error states
  const isLoading = currentCategory === 'trash'
    ? isLoadingTrash
    : currentCategory === 'collection'
      ? isLoadingCollection
      : isLoadingNotes;
  const isError = currentCategory === 'trash'
    ? isErrorTrash
    : currentCategory === 'collection'
      ? isErrorCollection
      : isErrorNotes;
  const error = currentCategory === 'trash'
    ? errorTrash
    : currentCategory === 'collection'
      ? errorCollection
      : errorNotes;
  const refetch = currentCategory === 'trash'
    ? refetchTrash
    : currentCategory === 'collection'
      ? refetchCollection
      : refetchNotes;

  // Filter notes based on category
  const filterByCategory = useCallback((notes) => {
    const now = new Date();
    const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

    switch (currentCategory) {
      case 'inbox':
        // Recent notes (last 7 days)
        return notes.filter(note => new Date(note.created_at) > sevenDaysAgo);

      case 'smart':
        // AI-generated notes (have associated images or is_standalone = false)
        return notes.filter(note =>
          (note.image_ids && note.image_ids.length > 0) ||
          note.is_standalone === false
        );

      case 'manual':
        // User-created notes (no images and is_standalone = true)
        return notes.filter(note =>
          (!note.image_ids || note.image_ids.length === 0) &&
          note.is_standalone !== false
        );

      case 'daily':
        // Daily/journal notes (title pattern matching)
        return notes.filter(note =>
          note.title?.startsWith('Daily Note') ||
          note.title?.match(/^\d{4}-\d{2}-\d{2}/) ||
          note.title?.toLowerCase().includes('journal')
        );

      case 'favorites':
        // Favorited notes (needs backend field - placeholder)
        return notes.filter(note => note.is_favorite);

      case 'review':
        // AI-generated notes that need review (have images, possibly need attention)
        return notes.filter(note =>
          (note.image_ids && note.image_ids.length > 0) &&
          !note.is_reviewed
        );

      case 'trash':
        // Trashed notes - already filtered by separate query
        return notes;

      case 'collection':
        // Collection notes - already filtered by separate query
        return notes;

      default:
        return notes;
    }
  }, [currentCategory]);

  // Filter by tag
  const filterByTag = useCallback((notes) => {
    if (!selectedTagFilter) return notes;
    return notes.filter(note =>
      note.tags?.some(tag => tag.name === selectedTagFilter)
    );
  }, [selectedTagFilter]);

  // Filter by search query
  const filterBySearch = useCallback((notes) => {
    if (!searchQuery?.trim()) return notes;
    const query = searchQuery.toLowerCase();
    return notes.filter(note =>
      note.title?.toLowerCase().includes(query) ||
      note.content?.toLowerCase().includes(query) ||
      note.tags?.some(tag => tag.name.toLowerCase().includes(query))
    );
  }, [searchQuery]);

  // Sort notes
  const sortNotes = useCallback((notes) => {
    const sorted = [...notes];
    const direction = sortOrder === 'desc' ? -1 : 1;

    sorted.sort((a, b) => {
      switch (sortBy) {
        case 'title':
          return direction * (a.title || '').localeCompare(b.title || '');
        case 'created':
          return direction * (new Date(a.created_at) - new Date(b.created_at));
        case 'updated':
        default:
          const aDate = new Date(a.updated_at || a.created_at);
          const bDate = new Date(b.updated_at || b.created_at);
          return direction * (aDate - bDate);
      }
    });

    return sorted;
  }, [sortBy, sortOrder]);

  // Apply all filters and sorting
  const notes = useMemo(() => {
    // Use trashedNotes when viewing trash, collectionData when viewing collection
    let filtered;
    if (currentCategory === 'trash') {
      filtered = trashedNotes;
    } else if (currentCategory === 'collection' && collectionData?.notes) {
      // Collection notes need to be mapped to match the enhanced note structure
      // The collection API returns minimal note info, so we need to find full notes
      const collectionNoteIds = new Set(collectionData.notes.map(n => n.id));
      filtered = rawNotes.filter(note => collectionNoteIds.has(note.id));
    } else {
      filtered = rawNotes;
    }
    filtered = filterByCategory(filtered);
    filtered = filterByTag(filtered);
    filtered = filterBySearch(filtered);
    filtered = sortNotes(filtered);
    return filtered;
  }, [rawNotes, trashedNotes, collectionData, currentCategory, filterByCategory, filterByTag, filterBySearch, sortNotes]);

  // Delete note mutation
  const deleteNote = useMutation({
    mutationFn: async (noteId) => {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/notes/${noteId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to delete note');
      return noteId;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notes-enhanced'] });
    }
  });

  return {
    notes,
    allNotes: rawNotes,
    isLoading,
    isError,
    error,
    refetch,
    deleteNote: deleteNote.mutate,
    isDeleting: deleteNote.isPending,
    totalCount: rawNotes.length,
    filteredCount: notes.length
  };
}

/**
 * useNoteSearch - Hook for searching notes
 */
export function useNoteSearch() {
  const searchMutation = useMutation({
    mutationFn: async ({ query, limit = 50 }) => {
      const token = localStorage.getItem('token');
      if (!token) throw new Error('Not authenticated');

      const params = new URLSearchParams({
        q: query,
        type: 'note',
        limit: limit.toString()
      });

      const response = await fetch(`${API_BASE}/search?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Search failed');
      return response.json();
    }
  });

  return {
    search: searchMutation.mutateAsync,
    searchResults: searchMutation.data || [],
    isSearching: searchMutation.isPending,
    searchError: searchMutation.error,
    clearResults: () => searchMutation.reset()
  };
}

export default useNotes;
