import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../../utils/api';

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
      return api.get('/albums/');
    },
    staleTime: 30000
  });

  // Create album mutation
  const createAlbum = useMutation({
    mutationFn: async ({ name, description }) => {
      return api.post('/albums/', { name, description });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['albums'] });
    }
  });

  // Update album mutation
  const updateAlbum = useMutation({
    mutationFn: async ({ albumId, name, description, cover_image_id }) => {
      return api.put(`/albums/${albumId}`, { name, description, cover_image_id });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['albums'] });
    }
  });

  // Delete album mutation
  const deleteAlbum = useMutation({
    mutationFn: async (albumId) => {
      return api.delete(`/albums/${albumId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['albums'] });
    }
  });

  // Add images to album mutation
  const addImagesToAlbum = useMutation({
    mutationFn: async ({ albumId, imageIds }) => {
      return api.post(`/albums/${albumId}/images`, { image_ids: imageIds });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['albums'] });
      queryClient.invalidateQueries({ queryKey: ['gallery-images'] });
    }
  });

  // Remove images from album mutation
  const removeImagesFromAlbum = useMutation({
    mutationFn: async ({ albumId, imageIds }) => {
      const response = await api.fetch(`/albums/${albumId}/images`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
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
      return api.get(`/albums/${albumId}/images`);
    },
    enabled: !!albumId,
    staleTime: 30000
  });

  return { images, isLoading, isError, error };
}

export default useAlbums;
