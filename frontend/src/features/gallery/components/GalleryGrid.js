import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Calendar } from 'lucide-react';
import PhotoThumbnail from './PhotoThumbnail';
import TimelineScrubber from './TimelineScrubber';
import ImageLightbox from './ImageLightbox';
import { useGalleryImages, useGalleryTags } from '../hooks/useGalleryImages';
import { useAlbums } from '../hooks/useAlbums';
import {
  calculateJustifiedLayout,
  groupImagesByDate,
  extractTimelineMarkers,
  preloadImageDimensions
} from '../utils/justifiedLayout';
import './GalleryGrid.css';

// API base URL
const API_BASE = 'http://localhost:8000';

/**
 * GalleryGrid - Center panel with justified photo grid
 * Features: Justified layout, date grouping, virtual scrolling, timeline scrubber
 */
function GalleryGrid({
  currentView,
  selectedAlbumId,
  selectedTags,
  sortBy,
  sortOrder,
  rowHeight,
  showFilenames,
  showDateHeaders,
  showTags,
  onNavigateToNote,
  onNavigateToAI,
  isSearchMode = false,
  searchResults = [],
  selectedImageId = null,
  onClearImageSelection
}) {
  const containerRef = useRef(null);
  const [containerWidth, setContainerWidth] = useState(0);
  const [selectedImage, setSelectedImage] = useState(null);
  const [activeTimelineMarker, setActiveTimelineMarker] = useState(null);
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
    renameImage
  } = useGalleryImages({ view: currentView, albumId: selectedAlbumId });

  // Fetch albums to get album name when viewing an album
  const { albums } = useAlbums();
  const currentAlbum = currentView === 'album' && selectedAlbumId
    ? albums.find(a => a.id === selectedAlbumId)
    : null;

  // Determine if we're in trash view or album view
  const isTrashView = currentView === 'trash';
  const isAlbumView = currentView === 'album' && selectedAlbumId;

  // Fetch tags for filtering (used for counts in context panel)
  useGalleryTags();

  // Create stable key from image IDs to detect real changes
  const imageKey = useMemo(() => {
    return images.map(img => img.id).sort().join(',');
  }, [images]);

  // Preload image dimensions for justified layout
  useEffect(() => {
    // Skip if images haven't actually changed
    if (imageKey === lastImageKeyRef.current) {
      return;
    }

    // Skip if already loading
    if (loadingRef.current) {
      return;
    }

    lastImageKeyRef.current = imageKey;

    if (images.length === 0) {
      setImagesWithDimensions([]);
      setDimensionsLoaded(true);
      return;
    }

    // Check if images already have dimensions
    const needsDimensions = images.some(img => !img.width || !img.height);

    if (!needsDimensions) {
      setImagesWithDimensions(images);
      setDimensionsLoaded(true);
      return;
    }

    // Preload dimensions for images that don't have them
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
        // Fallback to images without dimensions
        setImagesWithDimensions(images);
        setDimensionsLoaded(true);
        loadingRef.current = false;
      });
  }, [images, imageKey]);

  // Measure container width
  useEffect(() => {
    const updateWidth = () => {
      if (containerRef.current) {
        // Account for timeline scrubber width (60px) and padding
        const width = containerRef.current.offsetWidth - 80;
        setContainerWidth(width);
      }
    };

    updateWidth();
    window.addEventListener('resize', updateWidth);

    // Use ResizeObserver for more accurate measurements
    const observer = new ResizeObserver(updateWidth);
    if (containerRef.current) {
      observer.observe(containerRef.current);
    }

    return () => {
      window.removeEventListener('resize', updateWidth);
      observer.disconnect();
    };
  }, []);

  // Filter images by tags (use images with dimensions for layout)
  // Merge latest properties from images into imagesWithDimensions for optimistic updates
  // When in search mode, use searchResults instead
  const filteredImages = useMemo(() => {
    // In search mode, use search results directly
    if (isSearchMode && searchResults.length > 0) {
      if (selectedTags.length === 0) return searchResults;
      return searchResults.filter(img =>
        img.tags?.some(tag => selectedTags.includes(tag.id))
      );
    }

    let sourceImages;
    if (dimensionsLoaded && imagesWithDimensions.length > 0) {
      // Create a map of latest image properties for quick lookup
      const latestPropsMap = new Map(images.map(img => [img.id, img]));
      // Merge latest properties (like is_favorite) into imagesWithDimensions
      sourceImages = imagesWithDimensions.map(img => {
        const latest = latestPropsMap.get(img.id);
        if (latest) {
          return { ...img, is_favorite: latest.is_favorite, tags: latest.tags };
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

  // Group images by date
  const dateGroups = useMemo(() => {
    if (!showDateHeaders) {
      return [{ key: 'all', label: '', images: sortedImages }];
    }
    return groupImagesByDate(sortedImages);
  }, [sortedImages, showDateHeaders]);

  // Extract timeline markers
  const timelineMarkers = useMemo(() => {
    return extractTimelineMarkers(sortedImages);
  }, [sortedImages]);

  // Calculate justified layout for each group
  const layoutRows = useMemo(() => {
    if (containerWidth <= 0) return [];

    const rows = [];

    dateGroups.forEach(group => {
      // Add date header row
      if (showDateHeaders && group.label) {
        rows.push({
          type: 'date-header',
          key: `header-${group.key}`,
          label: group.label,
          date: group.date
        });
      }

      // Calculate justified layout for this group's images
      const justifiedRows = calculateJustifiedLayout(group.images, containerWidth, {
        targetRowHeight: rowHeight,
        gap: 4
      });

      // Add image rows
      justifiedRows.forEach((row, rowIndex) => {
        // Get date from group or from first image in row (for when showDateHeaders is false)
        const rowDate = group.date || (row.images[0]?.uploaded_at);
        rows.push({
          type: 'image-row',
          key: `row-${group.key}-${rowIndex}`,
          images: row.images,
          height: row.height,
          width: row.width,
          date: rowDate
        });
      });
    });

    return rows;
  }, [dateGroups, containerWidth, rowHeight, showDateHeaders]);

  // Virtual scrolling
  const virtualizer = useVirtualizer({
    count: layoutRows.length,
    getScrollElement: () => containerRef.current,
    estimateSize: (index) => {
      const row = layoutRows[index];
      if (row?.type === 'date-header') return 48;
      return row?.height || rowHeight;
    },
    overscan: 3
  });

  // Track scroll position for timeline
  const handleScroll = useCallback(() => {
    if (!containerRef.current) return;

    const items = virtualizer.getVirtualItems();

    // Find first visible image row
    for (const item of items) {
      const row = layoutRows[item.index];
      if (row?.type === 'image-row' && row.date) {
        const date = new Date(row.date);
        const markerKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        setActiveTimelineMarker(markerKey);
        break;
      }
    }
  }, [layoutRows, virtualizer]);

  // Set initial active marker when images load
  useEffect(() => {
    if (layoutRows.length > 0 && !activeTimelineMarker) {
      // Find first image row with a date
      for (const row of layoutRows) {
        if (row?.type === 'image-row' && row.date) {
          const date = new Date(row.date);
          const markerKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
          setActiveTimelineMarker(markerKey);
          break;
        }
      }
    }
  }, [layoutRows, activeTimelineMarker]);

  // Handle timeline marker click
  const handleTimelineClick = useCallback((marker) => {
    // Find first row with this date
    const rowIndex = layoutRows.findIndex(row => {
      if (row.date) {
        const date = new Date(row.date);
        const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        return key === marker.key;
      }
      return false;
    });

    if (rowIndex >= 0) {
      virtualizer.scrollToIndex(rowIndex, { align: 'start' });
    }
  }, [layoutRows, virtualizer]);

  // Lightbox handlers
  const openLightbox = useCallback((image) => {
    setSelectedImage(image);
  }, []);

  const closeLightbox = useCallback(() => {
    setSelectedImage(null);
  }, []);

  // Navigate between images in lightbox
  const handleLightboxNavigate = useCallback((direction) => {
    if (!selectedImage) return;

    const allImages = sortedImages;
    const currentIndex = allImages.findIndex(img => img.id === selectedImage.id);

    let newIndex;
    if (direction === 'prev') {
      newIndex = currentIndex > 0 ? currentIndex - 1 : allImages.length - 1;
    } else {
      newIndex = currentIndex < allImages.length - 1 ? currentIndex + 1 : 0;
    }

    setSelectedImage(allImages[newIndex]);
  }, [selectedImage, sortedImages]);

  // Sync selectedImage with updated images data (for optimistic updates)
  useEffect(() => {
    if (selectedImage && images.length > 0) {
      const updatedImage = images.find(img => img.id === selectedImage.id);
      if (updatedImage && (
        updatedImage.is_favorite !== selectedImage.is_favorite ||
        updatedImage.display_name !== selectedImage.display_name
      )) {
        setSelectedImage(updatedImage);
      }
    }
  }, [images, selectedImage]);

  // Open lightbox when navigating from another view with selectedImageId
  useEffect(() => {
    if (selectedImageId && images.length > 0) {
      const imageToOpen = images.find(img => img.id === selectedImageId);
      if (imageToOpen) {
        setSelectedImage(imageToOpen);
        // Clear the selection after opening
        if (onClearImageSelection) {
          onClearImageSelection();
        }
      }
    }
  }, [selectedImageId, images, onClearImageSelection]);

  // Handle image rename
  const handleRenameImage = useCallback((imageId, displayName) => {
    renameImage({ imageId, displayName });
  }, [renameImage]);

  // Get view title
  const getViewTitle = () => {
    if (isSearchMode) return 'Search Results';
    if (isAlbumView && currentAlbum) return currentAlbum.name;
    if (currentView === 'favorites') return 'Favorites';
    if (currentView === 'trash') return 'Trash';
    return 'All Photos';
  };

  // Empty state
  if (!isLoading && sortedImages.length === 0) {
    return (
      <div className="gallery-grid-empty">
        <div className="empty-icon">
          {isSearchMode ? '🔍' : isAlbumView ? '📁' : currentView === 'favorites' ? '💛' : currentView === 'trash' ? '🗑️' : '📷'}
        </div>
        <h3>
          {isSearchMode
            ? 'No results found'
            : isAlbumView
              ? `${currentAlbum?.name || 'Album'} is empty`
              : currentView === 'favorites'
                ? 'No favorites yet'
                : currentView === 'trash'
                  ? 'Trash is empty'
                  : 'No images yet'}
        </h3>
        <p>
          {isSearchMode
            ? 'Try different keywords or switch search type'
            : isAlbumView
              ? 'Add some images to this album'
              : currentView === 'favorites'
                ? 'Heart some images to see them here'
                : currentView === 'trash'
                  ? 'Deleted images will appear here'
                  : 'Upload some images to get started'}
        </p>
      </div>
    );
  }

  return (
    <div className="gallery-grid-container">
      {/* Header */}
      <div className="gallery-grid-header">
        <div className="header-info">
          <h2 className="view-title">{getViewTitle()}</h2>
          <span className="image-count">
            {sortedImages.length} {sortedImages.length === 1 ? 'photo' : 'photos'}
            {selectedTags.length > 0 && ' (filtered)'}
          </span>
        </div>
      </div>

      {/* Loading state */}
      {(isLoading || !dimensionsLoaded) && (
        <div className="gallery-loading">
          <div className="loading-spinner" />
          <span>{isLoading ? 'Loading photos...' : 'Preparing layout...'}</span>
        </div>
      )}

      {/* Grid area with timeline */}
      <div className="gallery-grid-area">
        {/* Timeline Scrubber - positioned outside scroll container */}
        <TimelineScrubber
          markers={timelineMarkers}
          activeMarker={activeTimelineMarker}
          onMarkerClick={handleTimelineClick}
        />

        {/* Scrollable grid */}
        <div
          ref={containerRef}
          className="gallery-scroll-container"
          onScroll={handleScroll}
        >
        <div
          style={{
            height: `${virtualizer.getTotalSize()}px`,
            width: '100%',
            position: 'relative'
          }}
        >
          {virtualizer.getVirtualItems().map((virtualItem) => {
            const row = layoutRows[virtualItem.index];
            if (!row) return null;

            return (
              <div
                key={virtualItem.key}
                data-index={virtualItem.index}
                ref={virtualizer.measureElement}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  transform: `translateY(${virtualItem.start}px)`
                }}
              >
                {row.type === 'date-header' ? (
                  <div className="date-header">
                    <Calendar size={16} />
                    <span>{row.label}</span>
                  </div>
                ) : (
                  <div
                    className="image-row"
                    style={{
                      display: 'flex',
                      gap: '4px',
                      height: row.height
                    }}
                  >
                    {row.images.map((image) => (
                      <PhotoThumbnail
                        key={image.id}
                        image={image}
                        width={image.finalWidth}
                        height={image.finalHeight}
                        showFilename={showFilenames}
                        showTags={showTags}
                        onClick={() => openLightbox(image)}
                        onFavorite={() => toggleFavorite(image.id)}
                        onDelete={() => moveToTrash(image.id)}
                        onRetry={() => retryAnalysis(image.id)}
                        onRestore={() => restoreFromTrash(image.id)}
                        onPermanentDelete={() => permanentDelete(image.id)}
                        isTrashView={isTrashView}
                      />
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
      </div>

      {/* Lightbox */}
      {selectedImage && (
        <ImageLightbox
          image={selectedImage}
          onClose={closeLightbox}
          onNavigate={handleLightboxNavigate}
          onNavigateToNote={onNavigateToNote}
          onNavigateToAI={onNavigateToAI}
          onFavorite={() => toggleFavorite(selectedImage.id)}
          onRetry={() => retryAnalysis(selectedImage.id)}
          onDelete={() => {
            moveToTrash(selectedImage.id);
            closeLightbox();
          }}
          onRename={handleRenameImage}
        />
      )}
    </div>
  );
}

export default GalleryGrid;
