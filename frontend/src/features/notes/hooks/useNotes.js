import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback, useMemo } from 'react';
import { useNoteContext } from './NoteContext';
import { api } from '../../../utils/api';

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
    queryFn: () => api.get('/notes-enhanced/'),
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
    queryFn: () => api.get('/notes/trash/'),
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
    queryFn: () => api.get(`/collections/${selectedCollectionId}`),
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
      case 'all':
        return notes;

      case 'inbox':
        return notes.filter(note => new Date(note.created_at) > sevenDaysAgo);

      case 'smart':
        return notes.filter(note =>
          (note.image_ids && note.image_ids.length > 0) ||
          note.is_standalone === false
        );

      case 'manual':
        return notes.filter(note =>
          (!note.image_ids || note.image_ids.length === 0) &&
          note.is_standalone !== false
        );

      case 'daily':
        return notes.filter(note =>
          note.title?.startsWith('Daily Note') ||
          note.title?.match(/^\d{4}-\d{2}-\d{2}/) ||
          note.title?.toLowerCase().includes('journal')
        );

      case 'favorites':
        return notes.filter(note => note.is_favorite);

      case 'review':
        return notes.filter(note =>
          (note.image_ids && note.image_ids.length > 0) &&
          !note.is_reviewed
        );

      case 'trash':
        return notes;

      case 'collection':
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
        case 'custom':
          return 0; // Custom order is applied externally by useCustomNoteOrder
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
    let filtered;
    if (currentCategory === 'trash') {
      filtered = trashedNotes;
    } else if (currentCategory === 'collection' && collectionData?.notes) {
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
    mutationFn: (noteId) => api.delete(`/notes/${noteId}`),
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
      const params = new URLSearchParams({
        q: query,
        type: 'note',
        limit: limit.toString()
      });
      return api.get(`/search?${params}`);
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
