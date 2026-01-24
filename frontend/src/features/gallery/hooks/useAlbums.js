import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

const API_BASE = 'http://localhost:8000';

/**
 * Hook for fetching and managing albums
 */
export function useAlbums() {
  const queryClient = useQueryClient();

  // Fetch all albums
  const {
    data: albumsData,
    isLoading,
    isError,
    error,
    refetch
  } = useQuery({
    queryKey: ['albums'],
    queryFn: async () => {
      const token = localStorage.getItem('token');
      if (!token) throw new Error('Not authenticated');

      const response = await fetch(`${API_BASE}/albums/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          localStorage.removeItem('token');
          localStorage.removeItem('username');
          window.location.reload();
        }
        throw new Error('Failed to fetch albums');
      }

      return response.json();
    },
    staleTime: 30000
  });

  // Create album mutation
  const createAlbum = useMutation({
    mutationFn: async ({ name, description }) => {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/albums/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name, description })
      });
      if (!response.ok) throw new Error('Failed to create album');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['albums'] });
    }
  });

  // Update album mutation
  const updateAlbum = useMutation({
    mutationFn: async ({ albumId, name, description, cover_image_id }) => {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/albums/${albumId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name, description, cover_image_id })
      });
      if (!response.ok) throw new Error('Failed to update album');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['albums'] });
    }
  });

  // Delete album mutation
  const deleteAlbum = useMutation({
    mutationFn: async (albumId) => {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/albums/${albumId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to delete album');
      return true;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['albums'] });
    }
  });

  // Add images to album mutation
  const addImagesToAlbum = useMutation({
    mutationFn: async ({ albumId, imageIds }) => {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/albums/${albumId}/images`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ image_ids: imageIds })
      });
      if (!response.ok) throw new Error('Failed to add images to album');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['albums'] });
      queryClient.invalidateQueries({ queryKey: ['gallery-images'] });
    }
  });

  // Remove images from album mutation
  const removeImagesFromAlbum = useMutation({
    mutationFn: async ({ albumId, imageIds }) => {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/albums/${albumId}/images`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ image_ids: imageIds })
      });
      if (!response.ok) throw new Error('Failed to remove images from album');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['albums'] });
      queryClient.invalidateQueries({ queryKey: ['gallery-images'] });
    }
  });

  return {
    albums: albumsData?.albums || [],
    total: albumsData?.total || 0,
    isLoading,
    isError,
    error,
    refetch,
    createAlbum: createAlbum.mutate,
    updateAlbum: updateAlbum.mutate,
    deleteAlbum: deleteAlbum.mutate,
    addImagesToAlbum: addImagesToAlbum.mutate,
    removeImagesFromAlbum: removeImagesFromAlbum.mutate,
    isCreating: createAlbum.isPending,
    isUpdating: updateAlbum.isPending,
    isDeleting: deleteAlbum.isPending
  };
}

/**
 * Hook for fetching images in a specific album
 */
export function useAlbumImages(albumId) {
  const {
    data: images = [],
    isLoading,
    isError,
    error
  } = useQuery({
    queryKey: ['album-images', albumId],
    queryFn: async () => {
      if (!albumId) return [];

      const token = localStorage.getItem('token');
      if (!token) throw new Error('Not authenticated');

      const response = await fetch(`${API_BASE}/albums/${albumId}/images`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Failed to fetch album images');
      return response.json();
    },
    enabled: !!albumId,
    staleTime: 30000
  });

  return { images, isLoading, isError, error };
}

export default useAlbums;
