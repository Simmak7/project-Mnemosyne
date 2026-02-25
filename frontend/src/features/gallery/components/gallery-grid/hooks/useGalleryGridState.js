import { useState, useEffect, useRef, useMemo } from 'react';
import { useGalleryImages, useGalleryTags } from '../../../hooks/useGalleryImages';
import { useAlbums } from '../../../hooks/useAlbums';
import { preloadImageDimensions } from '../../../utils/justifiedLayout';
import { API_URL as API_BASE } from '../../../../../utils/api';

/**
 * Hook for managing gallery grid state - image loading, dimensions, filtering
 */
export function useGalleryGridState({
  currentView,
  selectedAlbumId,
  selectedTags,
  sortBy,
  sortOrder,
  isSearchMode,
  searchResults,
}) {
  const [imagesWithDimensions, setImagesWithDimensions] = useState([]);
  const [dimensionsLoaded, setDimensionsLoaded] = useState(false);
  const loadingRef = useRef(false);
  const lastImageKeyRef = useRef('');

  // Fetch images
  const {
    images,
    isLoading,
    toggleFavorite,
    moveToTrash,
    restoreFromTrash,
    permanentDelete,
    retryAnalysis,
    renameImage,
  } = useGalleryImages({ view: currentView, albumId: selectedAlbumId });

  // Fetch albums to get album name when viewing an album
  const { albums } = useAlbums();
  const currentAlbum = currentView === 'album' && selectedAlbumId
    ? albums.find(a => a.id === selectedAlbumId)
    : null;

  // Determine view type
  const isTrashView = currentView === 'trash';
  const isAlbumView = currentView === 'album' && selectedAlbumId;

  // Fetch tags for filtering
  useGalleryTags();

  // Create stable key from image IDs to detect real changes
  const imageKey = useMemo(() => {
    return images.map(img => img.id).sort().join(',');
  }, [images]);

  // Preload image dimensions for justified layout
  useEffect(() => {
    if (imageKey === lastImageKeyRef.current) return;
    if (loadingRef.current) return;

    lastImageKeyRef.current = imageKey;

    if (images.length === 0) {
      setImagesWithDimensions([]);
      setDimensionsLoaded(true);
      return;
    }

    const needsDimensions = images.some(img => !img.width || !img.height);

    if (!needsDimensions) {
      setImagesWithDimensions(images);
      setDimensionsLoaded(true);
      return;
    }

    loadingRef.current = true;
    setDimensionsLoaded(false);
    const getImageUrl = (image) => `${API_BASE}/image/${image.id}`;

    preloadImageDimensions(images, getImageUrl)
      .then(imagesWithDims => {
        setImagesWithDimensions(imagesWithDims);
        setDimensionsLoaded(true);
        loadingRef.current = false;
      })
      .catch(() => {
        setImagesWithDimensions(images);
        setDimensionsLoaded(true);
        loadingRef.current = false;
      });
  }, [images, imageKey]);

  // Filter images by tags
  const filteredImages = useMemo(() => {
    if (isSearchMode && searchResults.length > 0) {
      if (selectedTags.length === 0) return searchResults;
      return searchResults.filter(img =>
        img.tags?.some(tag => selectedTags.includes(tag.id))
      );
    }

    let sourceImages;
    if (dimensionsLoaded && imagesWithDimensions.length > 0) {
      const latestPropsMap = new Map(images.map(img => [img.id, img]));
      sourceImages = imagesWithDimensions.map(img => {
        const latest = latestPropsMap.get(img.id);
        if (latest) {
          return { ...img, is_favorite: latest.is_favorite, tags: latest.tags, ai_analysis_status: latest.ai_analysis_status };
        }
        return img;
      });
    } else {
      sourceImages = images;
    }

    if (selectedTags.length === 0) return sourceImages;
    return sourceImages.filter(img =>
      img.tags?.some(tag => selectedTags.includes(tag.id))
    );
  }, [images, imagesWithDimensions, dimensionsLoaded, selectedTags, isSearchMode, searchResults]);

  // Sort images
  const sortedImages = useMemo(() => {
    const sorted = [...filteredImages];

    sorted.sort((a, b) => {
      let comparison = 0;

      if (sortBy === 'date') {
        comparison = new Date(b.uploaded_at) - new Date(a.uploaded_at);
      } else if (sortBy === 'name') {
        comparison = a.filename.localeCompare(b.filename);
      } else if (sortBy === 'size') {
        comparison = (b.file_size || 0) - (a.file_size || 0);
      }

      return sortOrder === 'asc' ? -comparison : comparison;
    });

    return sorted;
  }, [filteredImages, sortBy, sortOrder]);

  return {
    images,
    sortedImages,
    isLoading,
    dimensionsLoaded,
    isTrashView,
    isAlbumView,
    currentAlbum,
    toggleFavorite,
    moveToTrash,
    restoreFromTrash,
    permanentDelete,
    retryAnalysis,
    renameImage,
  };
}
