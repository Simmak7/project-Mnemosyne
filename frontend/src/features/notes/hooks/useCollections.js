import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../../utils/api';

/**
 * Hook for fetching and managing note collections
 */
export function useCollections() {
  const queryClient = useQueryClient();

  // Fetch all collections
  const {
    data: collections = [],
    isLoading,
    isError,
    error,
    refetch
  } = useQuery({
    queryKey: ['collections'],
    queryFn: () => api.get('/collections/'),
    staleTime: 30000
  });

  // Create collection mutation
  const createCollection = useMutation({
    mutationFn: async ({ name, description, icon, color }) => {
      return api.post('/collections/', { name, description, icon, color });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
    }
  });

  // Update collection mutation
  const updateCollection = useMutation({
    mutationFn: async ({ collectionId, name, description, icon, color }) => {
      return api.put(`/collections/${collectionId}`, { name, description, icon, color });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
    }
  });

  // Delete collection mutation
  const deleteCollection = useMutation({
    mutationFn: async (collectionId) => {
      return api.delete(`/collections/${collectionId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
    }
  });

  // Add note to collection mutation
  const addNoteToCollection = useMutation({
    mutationFn: async ({ collectionId, noteId }) => {
      return api.post(`/collections/${collectionId}/notes`, { note_id: noteId });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
      queryClient.invalidateQueries({ queryKey: ['notes-enhanced'] });
      queryClient.invalidateQueries({ queryKey: ['note-collections'] });
    }
  });

  // Remove note from collection mutation
  const removeNoteFromCollection = useMutation({
    mutationFn: async ({ collectionId, noteId }) => {
      return api.delete(`/collections/${collectionId}/notes/${noteId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
      queryClient.invalidateQueries({ queryKey: ['notes-enhanced'] });
      queryClient.invalidateQueries({ queryKey: ['note-collections'] });
    }
  });

  return {
    collections,
    isLoading,
    isError,
    error,
    refetch,
    createCollection: createCollection.mutate,
    updateCollection: updateCollection.mutate,
    deleteCollection: deleteCollection.mutate,
    addNoteToCollection: addNoteToCollection.mutate,
    removeNoteFromCollection: removeNoteFromCollection.mutate,
    isCreating: createCollection.isPending,
    isUpdating: updateCollection.isPending,
    isDeleting: deleteCollection.isPending
  };
}

/**
 * Hook for fetching a single collection with notes
 */
export function useCollectionNotes(collectionId) {
  const {
    data,
    isLoading,
    isError,
    error
  } = useQuery({
    queryKey: ['collection', collectionId],
    queryFn: () => collectionId ? api.get(`/collections/${collectionId}`) : null,
    enabled: !!collectionId,
    staleTime: 30000
  });

  return {
    collection: data,
    notes: data?.notes || [],
    isLoading,
    isError,
    error
  };
}

/**
 * Hook for fetching collections that contain a specific note
 */
export function useNoteCollections(noteId) {
  const {
    data: collections = [],
    isLoading,
    isError,
    error
  } = useQuery({
    queryKey: ['note-collections', noteId],
    queryFn: () => noteId ? api.get(`/collections/note/${noteId}`) : [],
    enabled: !!noteId,
    staleTime: 30000
  });

  return { collections, isLoading, isError, error };
}

export default useCollections;
