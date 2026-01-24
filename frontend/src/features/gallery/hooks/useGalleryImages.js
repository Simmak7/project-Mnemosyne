import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

const API_BASE = 'http://localhost:8000';

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
      const token = localStorage.getItem('token');
      if (!token) throw new Error('Not authenticated');

      let url = `${API_BASE}/images/?skip=${skip}&limit=${limit}`;

      // Adjust URL based on view
      if (view === 'favorites') {
        url = `${API_BASE}/images/favorites/?skip=${skip}&limit=${limit}`;
      } else if (view === 'trash') {
        url = `${API_BASE}/images/trash/?skip=${skip}&limit=${limit}`;
      } else if (view === 'album' && albumId) {
        url = `${API_BASE}/albums/${albumId}/images?skip=${skip}&limit=${limit}`;
      }

      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          localStorage.removeItem('token');
          localStorage.removeItem('username');
          window.location.reload();
        }
        throw new Error('Failed to fetch images');
      }

      return response.json();
    },
    staleTime: 30000,
    refetchOnWindowFocus: false
  });

  // Toggle favorite mutation with optimistic updates
  const toggleFavorite = useMutation({
    mutationFn: async (imageId) => {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/images/${imageId}/favorite`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to toggle favorite');
      return { imageId, data: await response.json() };
    },
    onMutate: async (imageId) => {
      // Cancel any outgoing refetches to avoid overwriting optimistic update
      await queryClient.cancelQueries({ queryKey: ['gallery-images'] });

      // Snapshot all gallery-images queries for potential rollback
      const previousQueries = queryClient.getQueriesData({ queryKey: ['gallery-images'] });

      // Optimistically update all cached gallery-images queries
      queryClient.setQueriesData({ queryKey: ['gallery-images'] }, (oldData) => {
        if (!oldData || !Array.isArray(oldData)) return oldData;
        return oldData.map(img =>
          img.id === imageId ? { ...img, is_favorite: !img.is_favorite } : img
        );
      });

      // Return context with previous data for rollback
      return { previousQueries, imageId };
    },
    onError: (err, imageId, context) => {
      // Roll back to previous state on error
      if (context?.previousQueries) {
        context.previousQueries.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
    },
    onSuccess: (result) => {
      // Update cache with actual server response (no refetch needed)
      const { imageId, data: updatedImage } = result;
      queryClient.setQueriesData({ queryKey: ['gallery-images'] }, (oldData) => {
        if (!oldData || !Array.isArray(oldData)) return oldData;
        return oldData.map(img =>
          img.id === imageId ? { ...img, is_favorite: updatedImage.is_favorite } : img
        );
      });
    }
    // No onSettled - we don't want to refetch and overwrite the update
  });

  // Move to trash mutation
  const moveToTrash = useMutation({
    mutationFn: async (imageId) => {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/images/${imageId}/trash`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to move to trash');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gallery-images'] });
    }
  });

  // Restore from trash mutation
  const restoreFromTrash = useMutation({
    mutationFn: async (imageId) => {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/images/${imageId}/restore`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to restore image');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gallery-images'] });
    }
  });

  // Permanent delete mutation
  const permanentDelete = useMutation({
    mutationFn: async (imageId) => {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/images/${imageId}/permanent`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to delete image');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gallery-images'] });
    }
  });

  // Retry AI analysis mutation
  const retryAnalysis = useMutation({
    mutationFn: async (imageId) => {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/retry-image/${imageId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      if (!response.ok) throw new Error('Failed to retry analysis');
      return response.json();
    },
    onSuccess: () => {
      // Refetch after a delay to see updated status
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['gallery-images'] });
      }, 2000);
    }
  });

  // Rename image mutation with optimistic updates
  const renameImage = useMutation({
    mutationFn: async ({ imageId, displayName }) => {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/images/${imageId}/rename`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ display_name: displayName })
      });
      if (!response.ok) throw new Error('Failed to rename image');
      return { imageId, data: await response.json() };
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
        context.previousQueries.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
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
      const token = localStorage.getItem('token');
      if (!token) throw new Error('Not authenticated');

      const response = await fetch(`${API_BASE}/tags/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Failed to fetch tags');
      return response.json();
    },
    staleTime: 60000
  });

  return { tags, isLoading, error };
}

/**
 * Hook for searching gallery images
 */
export function useGallerySearch() {
  const queryClient = useQueryClient();

  const searchMutation = useMutation({
    mutationFn: async ({ query, searchType = 'text', limit = 50 }) => {
      const token = localStorage.getItem('token');
      if (!token) throw new Error('Not authenticated');

      const params = new URLSearchParams({
        q: query,
        search_type: searchType,
        limit: limit.toString()
      });

      const response = await fetch(`${API_BASE}/images/search/?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          localStorage.removeItem('token');
          localStorage.removeItem('username');
          window.location.reload();
        }
        throw new Error('Search failed');
      }

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

export default useGalleryImages;
