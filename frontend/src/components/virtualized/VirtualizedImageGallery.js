import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Calendar, Sparkles, RefreshCw, Trash2, X } from 'lucide-react';
import LazyImage from '../layout/LazyImage';
import './VirtualizedImageGallery.css';

function VirtualizedImageGallery({ selectedImageId, refreshTrigger, onViewNote }) {
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [columnCount, setColumnCount] = useState(4);
  const [allTags, setAllTags] = useState([]);
  const [selectedTags, setSelectedTags] = useState([]);
  const [showTagFilter, setShowTagFilter] = useState(false);
  const [retryingImages, setRetryingImages] = useState(new Set());
  const [deleteConfirmation, setDeleteConfirmation] = useState(null); // { imageId, imageName }
  const [deletingImages, setDeletingImages] = useState(new Set());
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState(''); // 'success' or 'error'
  const parentRef = useRef(null);

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

  // Fetch images from API
  const fetchImages = useCallback(async (pageNum) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        console.error('No token found');
        return [];
      }

      const response = await fetch(
        `http://localhost:8000/images/?skip=${(pageNum - 1) * 50}&limit=50`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        return data;
      } else if (response.status === 401 || response.status === 403) {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        window.location.reload();
      }
      return [];
    } catch (error) {
      console.error('Error fetching images:', error);
      return [];
    }
  }, []);

  // Fetch tags
  const fetchTags = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await fetch('http://localhost:8000/tags/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setAllTags(data);
      }
    } catch (error) {
      console.error('Error fetching tags:', error);
    }
  }, []);

  // Retry AI analysis for a failed image
  const retryImageAnalysis = useCallback(async (imageId) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setMessage('Please login to retry image analysis');
        setMessageType('error');
        setTimeout(() => setMessage(''), 3000);
        return;
      }

      // Add to retrying set
      setRetryingImages(prev => new Set([...prev, imageId]));

      // Update image status to processing in local state
      setImages(prevImages =>
        prevImages.map(img =>
          img.id === imageId ? { ...img, ai_analysis_status: 'processing' } : img
        )
      );

      const response = await fetch(`http://localhost:8000/retry-image/${imageId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Retry successful:', data);

        // Show success message
        setMessage('AI analysis re-queued successfully! Processing...');
        setMessageType('success');
        setTimeout(() => setMessage(''), 3000);

        // The task is now queued/processing, we'll rely on polling or refresh to see the result
        setTimeout(() => {
          // Remove from retrying set after a delay
          setRetryingImages(prev => {
            const newSet = new Set(prev);
            newSet.delete(imageId);
            return newSet;
          });
        }, 2000);
      } else if (response.status === 401 || response.status === 403) {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        window.location.reload();
      } else {
        const errorData = await response.json();
        console.error('Retry failed:', errorData);

        // Show error message
        setMessage(`Failed to retry: ${errorData.detail || 'Unknown error'}`);
        setMessageType('error');
        setTimeout(() => setMessage(''), 5000);

        // Revert status back to failed
        setImages(prevImages =>
          prevImages.map(img =>
            img.id === imageId ? { ...img, ai_analysis_status: 'failed' } : img
          )
        );

        setRetryingImages(prev => {
          const newSet = new Set(prev);
          newSet.delete(imageId);
          return newSet;
        });
      }
    } catch (error) {
      console.error('Error retrying image analysis:', error);

      // Show error message
      setMessage(`Network error: ${error.message}`);
      setMessageType('error');
      setTimeout(() => setMessage(''), 5000);

      // Revert status back to failed
      setImages(prevImages =>
        prevImages.map(img =>
          img.id === imageId ? { ...img, ai_analysis_status: 'failed' } : img
        )
      );

      setRetryingImages(prev => {
        const newSet = new Set(prev);
        newSet.delete(imageId);
        return newSet;
      });
    }
  }, []);

  // Delete image handler
  const handleDeleteImage = async (imageId) => {
    const token = localStorage.getItem('token');
    if (!token) {
      console.error('No token found');
      return;
    }

    setDeletingImages(prev => new Set(prev).add(imageId));

    try {
      const response = await fetch(`http://localhost:8000/images/${imageId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        }
      });

      if (response.ok) {
        // Remove image from local state
        setImages(prevImages => prevImages.filter(img => img.id !== imageId));
        setDeleteConfirmation(null);
        console.log('Image deleted successfully');
      } else if (response.status === 401 || response.status === 403) {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        window.location.reload();
      } else {
        const errorData = await response.json();
        console.error('Delete failed:', errorData);
        alert('Failed to delete image: ' + (errorData.detail || 'Unknown error'));
      }
    } catch (error) {
      console.error('Delete failed:', error);
      alert('Failed to delete image. Please try again.');
    } finally {
      setDeletingImages(prev => {
        const newSet = new Set(prev);
        newSet.delete(imageId);
        return newSet;
      });
    }
  };

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
  }, [fetchImages, fetchTags]);

  // Refresh when refreshTrigger changes (e.g., after image upload)
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
  }, [refreshTrigger, fetchImages, fetchTags]);

  // Poll for processing images - check every 5 seconds
  useEffect(() => {
    const hasProcessingImages = images.some(img => img.ai_analysis_status === 'processing');

    if (!hasProcessingImages) {
      return; // No polling needed
    }

    const interval = setInterval(async () => {
      const refreshedImages = await fetchImages(page);
      setImages(refreshedImages);
    }, 5000); // Poll every 5 seconds

    return () => clearInterval(interval);
  }, [images, page, fetchImages]);

  // Auto-open image from search results
  useEffect(() => {
    if (selectedImageId && images.length > 0) {
      const imageToOpen = images.find(img => img.id === selectedImageId);
      if (imageToOpen) {
        setSelectedImage(imageToOpen);
      }
    }
  }, [selectedImageId, images]);

  // Load more images
  const loadMore = useCallback(async () => {
    if (loading || !hasMore) return;

    setLoading(true);
    const nextPage = page + 1;
    const newImages = await fetchImages(nextPage);

    if (newImages.length === 0) {
      setHasMore(false);
    } else {
      setImages(prev => [...prev, ...newImages]);
      setPage(nextPage);
      setHasMore(newImages.length === 50);
    }
    setLoading(false);
  }, [fetchImages, page, loading, hasMore]);

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
      // Add date header row
      rows.push({ type: 'date-header', date });

      // Add image rows for this date
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

  // Handle scroll for infinite loading
  const virtualItems = virtualizer.getVirtualItems();

  useEffect(() => {
    const lastItem = virtualItems[virtualItems.length - 1];

    if (!lastItem) return;

    if (
      lastItem.index >= dateGroupRows.length - 1 &&
      hasMore &&
      !loading
    ) {
      loadMore();
    }
  }, [virtualItems.length, dateGroupRows.length, hasMore, loading, loadMore]);

  // Lightbox handlers
  const openLightbox = (image) => {
    setSelectedImage(image);
    document.body.style.overflow = 'hidden';
  };

  const closeLightbox = () => {
    setSelectedImage(null);
    document.body.style.overflow = 'auto';
  };

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') {
      closeLightbox();
    }
  }, []);

  useEffect(() => {
    if (selectedImage) {
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [selectedImage, handleKeyDown]);

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

      {/* Message notification */}
      {message && (
        <div className={`gallery-message ${messageType}`}>
          {message}
        </div>
      )}

      {/* Tag Filter Panel */}
      {showTagFilter && (
        <div className="tag-filter-panel">
          <h4>Filter by Tags</h4>
          <div className="tag-filter-list">
            {allTags.map(tag => {
              const tagImageCount = images.filter(img =>
                img.tags?.some(t => t.id === tag.id)
              ).length;

              return (
                <label key={tag.id} className="tag-filter-item">
                  <input
                    type="checkbox"
                    checked={selectedTags.includes(tag.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedTags([...selectedTags, tag.id]);
                      } else {
                        setSelectedTags(selectedTags.filter(id => id !== tag.id));
                      }
                    }}
                  />
                  <span className="tag-name">#{tag.name}</span>
                  <span className="tag-count">{tagImageCount}</span>
                </label>
              );
            })}
          </div>
          {selectedTags.length > 0 && (
            <button
              className="clear-filters-btn"
              onClick={() => setSelectedTags([])}
            >
              Clear All Filters
            </button>
          )}
        </div>
      )}

      {images.length === 0 && !loading ? (
        <div className="empty-state">
          <div className="empty-icon">🖼️</div>
          <h3>No images yet</h3>
          <p>Start by uploading an image!</p>
        </div>
      ) : (
        <div
          ref={parentRef}
          className="gallery-scroll"
          style={{
            height: 'calc(100% - 80px)',
            overflow: 'auto',
          }}
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

              // Skip rendering if row is undefined (safety check)
              if (!isLoaderRow && !row) {
                return null;
              }

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
                        <div
                          key={image.id}
                          className="gallery-item"
                          onClick={() => openLightbox(image)}
                        >
                          <div className="image-wrapper">
                            <LazyImage
                              src={`http://localhost:8000/image/${image.id}`}
                              alt={image.filename}
                              className="gallery-image"
                              imageId={image.id}
                            />

                            {/* Processing Status Badge */}
                            {image.ai_analysis_status === 'processing' && (
                              <div className="processing-badge">
                                <Sparkles className="w-3 h-3 sparkle-animate" />
                                Analyzing
                              </div>
                            )}

                            {/* Failed Status Badge with Retry & Delete */}
                            {image.ai_analysis_status === 'failed' && (
                              <div className="failed-badge">
                                <span>Failed</span>
                                <button
                                  className="retry-badge-btn"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    retryImageAnalysis(image.id);
                                  }}
                                  disabled={retryingImages.has(image.id)}
                                  title="Retry AI analysis"
                                >
                                  <RefreshCw
                                    className={retryingImages.has(image.id) ? 'retry-spinning' : ''}
                                    size={14}
                                  />
                                </button>
                                <button
                                  className="delete-badge-btn"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setDeleteConfirmation({ imageId: image.id, imageName: image.filename });
                                  }}
                                  disabled={deletingImages.has(image.id)}
                                  title="Delete image"
                                >
                                  <Trash2 size={14} />
                                </button>
                              </div>
                            )}

                            {/* Delete Button (Always Visible on Hover) */}
                            <button
                              className="image-delete-btn"
                              onClick={(e) => {
                                e.stopPropagation();
                                setDeleteConfirmation({ imageId: image.id, imageName: image.filename });
                              }}
                              disabled={deletingImages.has(image.id)}
                              title="Delete image"
                            >
                              <Trash2 size={16} />
                            </button>

                            {/* Tags on Image */}
                            {image.tags && image.tags.length > 0 && (
                              <div className="image-tags">
                                {image.tags.slice(0, 3).map(tag => (
                                  <span key={tag.id} className="image-tag">
                                    #{tag.name}
                                  </span>
                                ))}
                                {image.tags.length > 3 && (
                                  <span className="image-tag-more">+{image.tags.length - 3}</span>
                                )}
                              </div>
                            )}

                            <div className="image-overlay">
                              <div className="image-info">
                                <p className="image-filename">{image.filename}</p>
                                <div className="status-info">
                                  <span className={`status-badge ${image.ai_analysis_status}`}>
                                    {image.ai_analysis_status}
                                  </span>
                                  {image.ai_analysis_status === 'failed' && !retryingImages.has(image.id) && (
                                    <button
                                      className="retry-btn"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        retryImageAnalysis(image.id);
                                      }}
                                      title="Retry AI analysis"
                                    >
                                      <RefreshCw size={14} />
                                      Retry
                                    </button>
                                  )}
                                  {retryingImages.has(image.id) && (
                                    <span className="retrying-text">Retrying...</span>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Lightbox Modal */}
      {selectedImage && (
        <div className="lightbox-overlay" onClick={closeLightbox}>
          <div className="lightbox-content" onClick={(e) => e.stopPropagation()}>
            <button
              className="lightbox-close"
              onClick={closeLightbox}
              aria-label="Close lightbox"
            >
              ×
            </button>
            <div className="lightbox-image-container">
              <img
                src={`http://localhost:8000/image/${selectedImage.id}`}
                alt={selectedImage.filename}
                className="lightbox-image"
              />
            </div>
            <div className="lightbox-info">
              <h3>{selectedImage.filename}</h3>
              <div className="lightbox-meta">
                <div className="lightbox-meta-row">
                  <span className="lightbox-meta-label">Status:</span>
                  <span className={`status-badge ${selectedImage.ai_analysis_status}`}>
                    {selectedImage.ai_analysis_status}
                  </span>
                </div>

                <div className="lightbox-meta-row">
                  <span className="lightbox-meta-label">Uploaded:</span>
                  <span className="lightbox-meta-value">
                    {new Date(selectedImage.uploaded_at).toLocaleString(undefined, {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </span>
                </div>

                {selectedImage.prompt && (
                  <div className="lightbox-meta-row lightbox-prompt-row">
                    <span className="lightbox-meta-label">Prompt:</span>
                    <span className="lightbox-meta-value">{selectedImage.prompt}</span>
                  </div>
                )}

                {selectedImage.tags && selectedImage.tags.length > 0 && (
                  <div className="lightbox-meta-row lightbox-tags-row">
                    <span className="lightbox-meta-label">Tags:</span>
                    <div className="lightbox-tags">
                      {selectedImage.tags.map(tag => (
                        <span key={tag.id} className="lightbox-tag">
                          #{tag.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {selectedImage.ai_analysis_status === 'failed' && (
                  <div className="lightbox-retry-section">
                    <button
                      className="retry-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        retryImageAnalysis(selectedImage.id);
                      }}
                      disabled={retryingImages.has(selectedImage.id)}
                    >
                      <RefreshCw size={14} className={retryingImages.has(selectedImage.id) ? 'retry-spinning' : ''} />
                      {retryingImages.has(selectedImage.id) ? 'Retrying...' : 'Retry Analysis'}
                    </button>
                  </div>
                )}

                {/* Display Notes */}
                {selectedImage.notes && selectedImage.notes.filter(Boolean).length > 0 && (
                  <div className="lightbox-notes-section">
                    <div className="lightbox-meta-label" style={{ marginTop: '1rem', marginBottom: '0.5rem' }}>
                      Generated Notes ({selectedImage.notes.filter(Boolean).length}):
                    </div>
                    {selectedImage.notes.filter(Boolean).map(note => {
                      const content = note.content || '';
                      return (
                        <div key={note.id} className="lightbox-note-card">
                          <div className="lightbox-note-title">{note.title || 'Untitled Note'}</div>
                          <div className="lightbox-note-preview">
                            {content.substring(0, 200)}
                            {content.length > 200 && '...'}
                          </div>
                          <button
                            className="view-note-btn"
                            onClick={() => {
                              if (onViewNote) {
                                onViewNote(note.id);
                                closeLightbox();
                              }
                            }}
                          >
                            View Full Note →
                          </button>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirmation && (
        <div className="delete-modal-overlay" onClick={() => setDeleteConfirmation(null)}>
          <div className="delete-modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="delete-modal-close" onClick={() => setDeleteConfirmation(null)}>
              <X size={20} />
            </button>

            <div className="delete-modal-header">
              <Trash2 size={32} className="delete-modal-icon" />
              <h3>Delete Image?</h3>
            </div>

            <div className="delete-modal-body">
              <p>Are you sure you want to delete this image?</p>
              <p className="delete-modal-filename">{deleteConfirmation.imageName}</p>
              <p className="delete-modal-warning">This action cannot be undone.</p>
            </div>

            <div className="delete-modal-actions">
              <button
                className="delete-modal-cancel-btn"
                onClick={() => setDeleteConfirmation(null)}
              >
                Cancel
              </button>
              <button
                className="delete-modal-confirm-btn"
                onClick={() => handleDeleteImage(deleteConfirmation.imageId)}
                disabled={deletingImages.has(deleteConfirmation.imageId)}
              >
                {deletingImages.has(deleteConfirmation.imageId) ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Memoize component to prevent unnecessary re-renders
export default React.memo(VirtualizedImageGallery);
