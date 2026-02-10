/**
 * VirtualizedImageGallery - Main gallery component with virtualization
 */
import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Calendar } from 'lucide-react';
import { useGalleryData } from './hooks/useGalleryData';
import TagFilterPanel from './components/TagFilterPanel';
import GalleryItem from './components/GalleryItem';
import LightboxModal from './components/LightboxModal';
import DeleteConfirmModal from './components/DeleteConfirmModal';
import '../VirtualizedImageGallery.css';

function VirtualizedImageGallery({ selectedImageId, refreshTrigger, onViewNote }) {
  const [selectedImage, setSelectedImage] = useState(null);
  const [columnCount, setColumnCount] = useState(4);
  const [selectedTags, setSelectedTags] = useState([]);
  const [showTagFilter, setShowTagFilter] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState(null);
  const parentRef = useRef(null);

  const {
    images, setImages,
    loading, setLoading,
    page, setPage,
    hasMore, setHasMore,
    allTags,
    retryingImages,
    deletingImages,
    message, messageType,
    fetchImages, fetchTags,
    retryImageAnalysis, handleDeleteImage,
    loadMore,
  } = useGalleryData();

  // Calculate column count based on window width
  useEffect(() => {
    const updateColumnCount = () => {
      const width = window.innerWidth;
      if (width < 640) setColumnCount(1);
      else if (width < 768) setColumnCount(2);
      else if (width < 1024) setColumnCount(3);
      else if (width < 1536) setColumnCount(4);
      else setColumnCount(5);
    };

    updateColumnCount();
    window.addEventListener('resize', updateColumnCount);
    return () => window.removeEventListener('resize', updateColumnCount);
  }, []);

  // Initial load
  useEffect(() => {
    const loadInitialImages = async () => {
      setLoading(true);
      const initialImages = await fetchImages(1);
      setImages(initialImages);
      setHasMore(initialImages.length === 50);
      setLoading(false);
    };
    loadInitialImages();
    fetchTags();
  }, [fetchImages, fetchTags, setImages, setLoading, setHasMore]);

  // Refresh when refreshTrigger changes
  useEffect(() => {
    if (refreshTrigger > 0) {
      const refreshImages = async () => {
        const refreshedImages = await fetchImages(1);
        setImages(refreshedImages);
        setHasMore(refreshedImages.length === 50);
        setPage(1);
      };
      refreshImages();
      fetchTags();
    }
  }, [refreshTrigger, fetchImages, fetchTags, setImages, setHasMore, setPage]);

  // Poll for processing images
  useEffect(() => {
    const hasProcessingImages = images.some(img => img.ai_analysis_status === 'processing');
    if (!hasProcessingImages) return;

    const interval = setInterval(async () => {
      const refreshedImages = await fetchImages(page);
      setImages(refreshedImages);
    }, 5000);

    return () => clearInterval(interval);
  }, [images, page, fetchImages, setImages]);

  // Auto-open image from search results
  useEffect(() => {
    if (selectedImageId && images.length > 0) {
      const imageToOpen = images.find(img => img.id === selectedImageId);
      if (imageToOpen) setSelectedImage(imageToOpen);
    }
  }, [selectedImageId, images]);

  // Filter images by selected tags
  const filteredImages = useMemo(() => {
    if (selectedTags.length === 0) return images;
    return images.filter(img =>
      img.tags?.some(tag => selectedTags.includes(tag.id))
    );
  }, [images, selectedTags]);

  // Group images by date
  const groupedImages = useMemo(() => {
    const groups = {};
    filteredImages.forEach(image => {
      const date = new Date(image.uploaded_at);
      const dateStr = date.toLocaleDateString(undefined, {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
        year: 'numeric'
      });
      if (!groups[dateStr]) groups[dateStr] = [];
      groups[dateStr].push(image);
    });
    return groups;
  }, [filteredImages]);

  // Organize grouped images into rows for virtualization
  const dateGroupRows = useMemo(() => {
    const rows = [];
    Object.entries(groupedImages).forEach(([date, dateImages]) => {
      rows.push({ type: 'date-header', date });
      for (let i = 0; i < dateImages.length; i += columnCount) {
        rows.push({
          type: 'image-row',
          images: dateImages.slice(i, i + columnCount)
        });
      }
    });
    return rows;
  }, [groupedImages, columnCount]);

  // Virtualizer for rows
  const virtualizer = useVirtualizer({
    count: hasMore ? dateGroupRows.length + 1 : dateGroupRows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: (index) => {
      const row = dateGroupRows[index];
      if (row?.type === 'date-header') return 50;
      return 280;
    },
    overscan: 2,
  });

  const virtualItems = virtualizer.getVirtualItems();

  // Handle scroll for infinite loading
  useEffect(() => {
    const lastItem = virtualItems[virtualItems.length - 1];
    if (!lastItem) return;

    if (lastItem.index >= dateGroupRows.length - 1 && hasMore && !loading) {
      loadMore();
    }
  }, [virtualItems.length, dateGroupRows.length, hasMore, loading, loadMore]);

  const openLightbox = (image) => setSelectedImage(image);
  const closeLightbox = () => setSelectedImage(null);

  const handleShowDeleteConfirm = (imageId, imageName) => {
    setDeleteConfirmation({ imageId, imageName });
  };

  const handleConfirmDelete = async (imageId) => {
    await handleDeleteImage(imageId, () => setDeleteConfirmation(null));
  };

  return (
    <div className="virtualized-image-gallery-container">
      <div className="gallery-header">
        <div className="gallery-header-left">
          <h2>Image Gallery</h2>
          <div className="gallery-count">
            {filteredImages.length} image{filteredImages.length !== 1 ? 's' : ''}
            {selectedTags.length > 0 && ` (filtered)`}
            {loading && ' (loading...)'}
          </div>
        </div>
        <button
          className="tag-filter-toggle"
          onClick={() => setShowTagFilter(!showTagFilter)}
        >
          {showTagFilter ? 'Hide' : 'Show'} Tag Filter
        </button>
      </div>

      {message && (
        <div className={`gallery-message ${messageType}`}>{message}</div>
      )}

      {showTagFilter && (
        <TagFilterPanel
          allTags={allTags}
          images={images}
          selectedTags={selectedTags}
          setSelectedTags={setSelectedTags}
        />
      )}

      {images.length === 0 && !loading ? (
        <div className="empty-state">
          <div className="empty-icon">&#128444;</div>
          <h3>No images yet</h3>
          <p>Start by uploading an image!</p>
        </div>
      ) : (
        <div
          ref={parentRef}
          className="gallery-scroll"
          style={{ height: 'calc(100% - 80px)', overflow: 'auto' }}
        >
          <div
            style={{
              height: `${virtualizer.getTotalSize()}px`,
              width: '100%',
              position: 'relative',
              padding: '1rem',
            }}
          >
            {virtualItems.map((virtualItem) => {
              const isLoaderRow = virtualItem.index >= dateGroupRows.length;
              const row = dateGroupRows[virtualItem.index];

              if (!isLoaderRow && !row) return null;

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
                    transform: `translateY(${virtualItem.start}px)`,
                    padding: '0 1rem',
                  }}
                >
                  {isLoaderRow ? (
                    hasMore ? (
                      <div className="gallery-loader">
                        <div className="loading-spinner"></div>
                        <span>Loading more images...</span>
                      </div>
                    ) : null
                  ) : row?.type === 'date-header' ? (
                    <div className="date-header">
                      <Calendar className="w-4 h-4" />
                      <span>{row.date}</span>
                    </div>
                  ) : (
                    <div
                      className="gallery-row"
                      style={{
                        display: 'grid',
                        gridTemplateColumns: `repeat(${columnCount}, 1fr)`,
                        gap: '1rem',
                      }}
                    >
                      {row?.images?.map((image) => (
                        <GalleryItem
                          key={image.id}
                          image={image}
                          onOpenLightbox={openLightbox}
                          onRetry={retryImageAnalysis}
                          onDelete={handleShowDeleteConfirm}
                          retryingImages={retryingImages}
                          deletingImages={deletingImages}
                        />
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {selectedImage && (
        <LightboxModal
          image={selectedImage}
          onClose={closeLightbox}
          onRetry={retryImageAnalysis}
          onViewNote={onViewNote}
          retryingImages={retryingImages}
        />
      )}

      {deleteConfirmation && (
        <DeleteConfirmModal
          imageId={deleteConfirmation.imageId}
          imageName={deleteConfirmation.imageName}
          onClose={() => setDeleteConfirmation(null)}
          onConfirm={handleConfirmDelete}
          isDeleting={deletingImages.has(deleteConfirmation.imageId)}
        />
      )}
    </div>
  );
}

export default React.memo(VirtualizedImageGallery);
