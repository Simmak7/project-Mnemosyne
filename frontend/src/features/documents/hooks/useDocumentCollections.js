/**
 * useDocumentCollections Hook
 * React Query hooks for document collection CRUD operations.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../../utils/api';

/**
 * Hook for fetching and managing document collections
 */
export function useDocCollections() {
  const queryClient = useQueryClient();

  const {
    data: collections = [],
    isLoading,
    isError,
    error,
    refetch
  } = useQuery({
    queryKey: ['document-collections'],
    queryFn: () => api.get('/document-collections/'),
    staleTime: 30000
  });

  const createCollection = useMutation({
    mutationFn: async ({ name, description, icon, color }) => {
      return api.post('/document-collections/', { name, description, icon, color });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document-collections'] });
    }
  });

  const updateCollection = useMutation({
    mutationFn: async ({ collectionId, name, description, icon, color }) => {
      return api.put(`/document-collections/${collectionId}`, { name, description, icon, color });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document-collections'] });
    }
  });

  const deleteCollection = useMutation({
    mutationFn: async (collectionId) => {
      return api.delete(`/document-collections/${collectionId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document-collections'] });
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    }
  });

  const addDocumentToCollection = useMutation({
    mutationFn: async ({ collectionId, documentId }) => {
      return api.post(`/document-collections/${collectionId}/documents`, { document_id: documentId });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document-collections'] });
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['doc-collections-for'] });
    }
  });

  const removeDocumentFromCollection = useMutation({
    mutationFn: async ({ collectionId, documentId }) => {
      return api.delete(`/document-collections/${collectionId}/documents/${documentId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document-collections'] });
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['doc-collections-for'] });
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
    addDocumentToCollection: addDocumentToCollection.mutate,
    removeDocumentFromCollection: removeDocumentFromCollection.mutate,
    isCreating: createCollection.isPending,
    isUpdating: updateCollection.isPending,
    isDeleting: deleteCollection.isPending
  };
}

/**
 * Hook for fetching collections that contain a specific document
 */
export function useDocCollectionsForDocument(documentId) {
  const {
    data: collections = [],
    isLoading,
    isError,
    error
  } = useQuery({
    queryKey: ['doc-collections-for', documentId],
    queryFn: () => documentId ? api.get(`/document-collections/document/${documentId}`) : [],
    enabled: !!documentId,
    staleTime: 30000
  });

  return { collections, isLoading, isError, error };
}

export default useDocCollections;
