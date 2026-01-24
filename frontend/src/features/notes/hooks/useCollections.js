import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

const API_BASE = 'http://localhost:8000';

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
    queryFn: async () => {
      const token = localStorage.getItem('token');
      if (!token) throw new Error('Not authenticated');

      const response = await fetch(`${API_BASE}/collections/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          localStorage.removeItem('token');
          localStorage.removeItem('username');
          window.location.reload();
        }
        throw new Error('Failed to fetch collections');
      }

      return response.json();
    },
    staleTime: 30000
  });

  // Create collection mutation
  const createCollection = useMutation({
    mutationFn: async ({ name, description, icon, color }) => {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/collections/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name, description, icon, color })
      });
      if (!response.ok) throw new Error('Failed to create collection');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
    }
  });

  // Update collection mutation
  const updateCollection = useMutation({
    mutationFn: async ({ collectionId, name, description, icon, color }) => {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/collections/${collectionId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name, description, icon, color })
      });
      if (!response.ok) throw new Error('Failed to update collection');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
    }
  });

  // Delete collection mutation
  const deleteCollection = useMutation({
    mutationFn: async (collectionId) => {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/collections/${collectionId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to delete collection');
      return true;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
    }
  });

  // Add note to collection mutation
  const addNoteToCollection = useMutation({
    mutationFn: async ({ collectionId, noteId }) => {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/collections/${collectionId}/notes`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ note_id: noteId })
      });
      if (!response.ok) throw new Error('Failed to add note to collection');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
      queryClient.invalidateQueries({ queryKey: ['notes-enhanced'] });
    }
  });

  // Remove note from collection mutation
  const removeNoteFromCollection = useMutation({
    mutationFn: async ({ collectionId, noteId }) => {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${API_BASE}/collections/${collectionId}/notes/${noteId}`,
        {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      if (!response.ok) throw new Error('Failed to remove note from collection');
      return true;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
      queryClient.invalidateQueries({ queryKey: ['notes-enhanced'] });
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
    queryFn: async () => {
      if (!collectionId) return null;

      const token = localStorage.getItem('token');
      if (!token) throw new Error('Not authenticated');

      const response = await fetch(`${API_BASE}/collections/${collectionId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Failed to fetch collection');
      return response.json();
    },
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
    queryFn: async () => {
      if (!noteId) return [];

      const token = localStorage.getItem('token');
      if (!token) throw new Error('Not authenticated');

      const response = await fetch(`${API_BASE}/collections/note/${noteId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Failed to fetch note collections');
      return response.json();
    },
    enabled: !!noteId,
    staleTime: 30000
  });

  return { collections, isLoading, isError, error };
}

export default useCollections;
