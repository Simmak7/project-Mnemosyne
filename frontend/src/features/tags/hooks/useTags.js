/**
 * useTags Hook
 *
 * React Query hook for fetching and managing tags.
 * Provides caching, automatic refetching, and mutation helpers.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tagsApi } from '../api';

/**
 * Query key for tags cache
 */
export const TAGS_QUERY_KEY = ['tags'];

/**
 * Hook for fetching and managing tags.
 *
 * @param {Object} options - Hook options
 * @param {boolean} options.enabled - Whether to enable the query (default: true)
 * @returns {Object} Query result with tags data and mutation functions
 */
export function useTags({ enabled = true } = {}) {
  const queryClient = useQueryClient();

  // Fetch all tags
  const tagsQuery = useQuery({
    queryKey: TAGS_QUERY_KEY,
    queryFn: tagsApi.fetchTags,
    enabled,
    staleTime: 30000, // 30 seconds
    cacheTime: 300000, // 5 minutes
  });

  // Create tag mutation
  const createTagMutation = useMutation({
    mutationFn: (name) => tagsApi.createTag(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TAGS_QUERY_KEY });
    },
  });

  // Add tag to image mutation
  const addTagToImageMutation = useMutation({
    mutationFn: ({ imageId, tagName }) => tagsApi.addTagToImage(imageId, tagName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TAGS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ['images'] });
    },
  });

  // Remove tag from image mutation
  const removeTagFromImageMutation = useMutation({
    mutationFn: ({ imageId, tagId }) => tagsApi.removeTagFromImage(imageId, tagId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TAGS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ['images'] });
    },
  });

  // Add tag to note mutation
  const addTagToNoteMutation = useMutation({
    mutationFn: ({ noteId, tagName }) => tagsApi.addTagToNote(noteId, tagName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TAGS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ['notes'] });
    },
  });

  // Remove tag from note mutation
  const removeTagFromNoteMutation = useMutation({
    mutationFn: ({ noteId, tagId }) => tagsApi.removeTagFromNote(noteId, tagId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TAGS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ['notes'] });
    },
  });

  return {
    // Query state
    tags: tagsQuery.data || [],
    isLoading: tagsQuery.isLoading,
    isError: tagsQuery.isError,
    error: tagsQuery.error,
    refetch: tagsQuery.refetch,

    // Mutations
    createTag: createTagMutation.mutateAsync,
    isCreatingTag: createTagMutation.isPending,

    addTagToImage: addTagToImageMutation.mutateAsync,
    isAddingTagToImage: addTagToImageMutation.isPending,

    removeTagFromImage: removeTagFromImageMutation.mutateAsync,
    isRemovingTagFromImage: removeTagFromImageMutation.isPending,

    addTagToNote: addTagToNoteMutation.mutateAsync,
    isAddingTagToNote: addTagToNoteMutation.isPending,

    removeTagFromNote: removeTagFromNoteMutation.mutateAsync,
    isRemovingTagFromNote: removeTagFromNoteMutation.isPending,
  };
}

export default useTags;
