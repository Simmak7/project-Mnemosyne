import { useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../../utils/api';

/**
 * Hook for fetching and managing gallery images
 */
export function useGalleryImages(options = {}) {
  const {
    view = 'all',
    albumId = null,
    skip = 0,
    limit = 100
  } = options;

  const queryClient = useQueryClient();

  // Build query key based on view
  const queryKey = ['gallery-images', view, albumId, skip, limit];

  // Fetch images
  const {
    data: images = [],
    isLoading,
    isError,
    error,
    refetch
  } = useQuery({
    queryKey,
    queryFn: async () => {
      let path = `/images/?skip=${skip}&limit=${limit}`;

      if (view === 'favorites') {
        path = `/images/favorites/?skip=${skip}&limit=${limit}`;
      } else if (view === 'trash') {
        path = `/images/trash/?skip=${skip}&limit=${limit}`;
      } else if (view === 'album' && albumId) {
        path = `/albums/${albumId}/images?skip=${skip}&limit=${limit}`;
      }

      return api.get(path);
    },
    staleTime: 30000,
    refetchOnWindowFocus: false
  });

  // Listen for gallery:refresh events to invalidate cache after upload
  useEffect(() => {
    const handleRefresh = () => {
      queryClient.invalidateQueries({ queryKey: ['gallery-images'] });
    };

    window.addEventListener('gallery:refresh', handleRefresh);
    return () => window.removeEventListener('gallery:refresh', handleRefresh);
  }, [queryClient]);

  // Toggle favorite mutation with optimistic updates
  const toggleFavorite = useMutation({
    mutationFn: async (imageId) => {
      const data = await api.post(`/images/${imageId}/favorite`);
      return { imageId, data };
    },
    onMutate: async (imageId) => {
      await queryClient.cancelQueries({ queryKey: ['gallery-images'] });
      const previousQueries = queryClient.getQueriesData({ queryKey: ['gallery-images'] });

      queryClient.setQueriesData({ queryKey: ['gallery-images'] }, (oldData) => {
        if (!oldData || !Array.isArray(oldData)) return oldData;
        return oldData.map(img =>
          img.id === imageId ? { ...img, is_favorite: !img.is_favorite } : img
        );
      });

      return { previousQueries, imageId };
    },
    onError: (err, imageId, context) => {
      if (context?.previousQueries) {
        context.previousQueries.forEach(([qk, data]) => {
          queryClient.setQueryData(qk, data);
        });
      }
    },
    onSuccess: (result) => {
      const { imageId, data: updatedImage } = result;
      queryClient.setQueriesData({ queryKey: ['gallery-images'] }, (oldData) => {
        if (!oldData || !Array.isArray(oldData)) return oldData;
        return oldData.map(img =>
          img.id === imageId ? { ...img, is_favorite: updatedImage.is_favorite } : img
        );
      });
    }
  });

  // Move to trash mutation
  const moveToTrash = useMutation({
    mutationFn: async (imageId) => {
      return api.post(`/images/${imageId}/trash`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gallery-images'] });
    }
  });

  // Restore from trash mutation
  const restoreFromTrash = useMutation({
    mutationFn: async (imageId) => {
      return api.post(`/images/${imageId}/restore`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gallery-images'] });
    }
  });

  // Permanent delete mutation
  const permanentDelete = useMutation({
    mutationFn: async (imageId) => {
      return api.delete(`/images/${imageId}/permanent`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gallery-images'] });
    }
  });

  // Retry AI analysis mutation with optimistic update
  const retryAnalysis = useMutation({
    mutationFn: async (imageId) => {
      return api.post(`/retry-image/${imageId}`);
    },
    onMutate: async (imageId) => {
      await queryClient.cancelQueries({ queryKey: ['gallery-images'] });
      const previousQueries = queryClient.getQueriesData({ queryKey: ['gallery-images'] });

      queryClient.setQueriesData({ queryKey: ['gallery-images'] }, (oldData) => {
        if (!oldData || !Array.isArray(oldData)) return oldData;
        return oldData.map(img =>
          img.id === imageId ? { ...img, ai_analysis_status: 'processing' } : img
        );
      });

      return { previousQueries };
    },
    onError: (err, imageId, context) => {
      if (context?.previousQueries) {
        context.previousQueries.forEach(([qk, data]) => {
          queryClient.setQueryData(qk, data);
        });
      }
    },
    onSuccess: () => {
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['gallery-images'] });
      }, 3000);
    }
  });

  // Rename image mutation with optimistic updates
  const renameImage = useMutation({
    mutationFn: async ({ imageId, displayName }) => {
      const data = await api.put(`/images/${imageId}/rename`, { display_name: displayName });
      return { imageId, data };
    },
    onMutate: async ({ imageId, displayName }) => {
      await queryClient.cancelQueries({ queryKey: ['gallery-images'] });
      const previousQueries = queryClient.getQueriesData({ queryKey: ['gallery-images'] });

      queryClient.setQueriesData({ queryKey: ['gallery-images'] }, (oldData) => {
        if (!oldData || !Array.isArray(oldData)) return oldData;
        return oldData.map(img =>
          img.id === imageId ? { ...img, display_name: displayName } : img
        );
      });

      return { previousQueries };
    },
    onError: (err, variables, context) => {
      if (context?.previousQueries) {
        context.previousQueries.forEach(([qk, data]) => {
          queryClient.setQueryData(qk, data);
        });
      }
    },
    onSuccess: (result) => {
      const { imageId, data: updatedImage } = result;
      queryClient.setQueriesData({ queryKey: ['gallery-images'] }, (oldData) => {
        if (!oldData || !Array.isArray(oldData)) return oldData;
        return oldData.map(img =>
          img.id === imageId ? { ...img, display_name: updatedImage.display_name } : img
        );
      });
    }
  });

  return {
    images,
    isLoading,
    isError,
    error,
    refetch,
    toggleFavorite: toggleFavorite.mutate,
    moveToTrash: moveToTrash.mutate,
    restoreFromTrash: restoreFromTrash.mutate,
    permanentDelete: permanentDelete.mutate,
    retryAnalysis: retryAnalysis.mutate,
    renameImage: renameImage.mutate,
    isToggling: toggleFavorite.isPending,
    isDeleting: moveToTrash.isPending || permanentDelete.isPending,
    isRenaming: renameImage.isPending
  };
}

/**
 * Hook for fetching all tags
 */
export function useGalleryTags() {
  const {
    data: tags = [],
    isLoading,
    error
  } = useQuery({
    queryKey: ['gallery-tags'],
    queryFn: async () => {
      return api.get('/tags/');
    },
    staleTime: 60000
  });

  return { tags, isLoading, error };
}

/**
 * Hook for searching gallery images
 */
export function useGallerySearch() {
  const searchMutation = useMutation({
    mutationFn: async ({ query, searchType = 'text', limit = 50 }) => {
      const params = new URLSearchParams({
        q: query,
        search_type: searchType,
        limit: limit.toString()
      });

      return api.get(`/images/search/?${params}`);
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

export default useGalleryImages;
