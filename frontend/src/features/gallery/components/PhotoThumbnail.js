import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Heart, Trash2, RefreshCw, Sparkles, Eye, RotateCcw, FolderPlus } from 'lucide-react';
import BlurHashPlaceholder from './BlurHashPlaceholder';
import AlbumPicker from './AlbumPicker';
import './PhotoThumbnail.css';

/**
 * PhotoThumbnail - Individual photo card in justified grid
 * Features: Lazy loading, blur hash placeholder, hover actions, status badges
 */
function PhotoThumbnail({
  image,
  width,
  height,
  showFilename,
  showTags = true,
  onClick,
  onFavorite,
  onDelete,
  onRetry,
  onRestore,
  onPermanentDelete,
  isTrashView = false
}) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [showAlbumPicker, setShowAlbumPicker] = useState(false);
  const [albumBtnRect, setAlbumBtnRect] = useState(null);
  const albumBtnRef = useRef(null);
  // Local state for instant favorite toggle feedback
  const [localFavorite, setLocalFavorite] = useState(image.is_favorite);

  // Sync local favorite state with prop changes
  useEffect(() => {
    setLocalFavorite(image.is_favorite);
  }, [image.is_favorite]);

  // Determine orientation for styling
  const orientation = image.orientation || (
    width && height
      ? (width / height < 0.9 ? 'portrait' : width / height > 1.1 ? 'landscape' : 'square')
      : 'landscape'
  );

  const handleLoad = useCallback(() => {
    setIsLoaded(true);
  }, []);

  const handleError = useCallback(() => {
    setHasError(true);
    setIsLoaded(true);
  }, []);

  const handleFavoriteClick = useCallback((e) => {
    e.stopPropagation();
    // Immediately toggle local state for instant feedback
    setLocalFavorite(prev => !prev);
    onFavorite?.();
  }, [onFavorite]);

  const handleDeleteClick = useCallback((e) => {
    e.stopPropagation();
    onDelete?.();
  }, [onDelete]);

  const handleRetryClick = useCallback((e) => {
    e.stopPropagation();
    onRetry?.();
  }, [onRetry]);

  const handleRestoreClick = useCallback((e) => {
    e.stopPropagation();
    onRestore?.();
  }, [onRestore]);

  const handlePermanentDeleteClick = useCallback((e) => {
    e.stopPropagation();
    onPermanentDelete?.();
  }, [onPermanentDelete]);

  const handleAlbumClick = useCallback((e) => {
    e.stopPropagation();
    // Get button position for portal positioning
    if (albumBtnRef.current) {
      const rect = albumBtnRef.current.getBoundingClientRect();
      setAlbumBtnRect(rect);
    }
    setShowAlbumPicker(true);
  }, []);

  const handleCloseAlbumPicker = useCallback(() => {
    setShowAlbumPicker(false);
  }, []);

  const isProcessing = image.ai_analysis_status === 'processing';
  const isFailed = image.ai_analysis_status === 'failed';

  return (
    <div
      className={`photo-thumbnail ${orientation} ${isHovered ? 'hovered' : ''}`}
      style={{ width, height }}
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Loading placeholder with blur hash (Phase 3) */}
      {!isLoaded && (
        <BlurHashPlaceholder
          hash={image.blur_hash}
          width={width}
          height={height}
          className={isLoaded ? 'fade-out' : ''}
        />
      )}

      {/* Image */}
      <img
        src={`http://localhost:8000/image/${image.id}`}
        alt={image.filename}
        className={`thumbnail-image ${isLoaded ? 'loaded' : ''}`}
        onLoad={handleLoad}
        onError={handleError}
        loading="lazy"
      />

      {/* Error state */}
      {hasError && (
        <div className="thumbnail-error">
          <Eye size={24} />
          <span>Failed to load</span>
        </div>
      )}

      {/* Status badges */}
      {isProcessing && (
        <div className="status-badge processing">
          <Sparkles size={12} className="sparkle-icon" />
          <span>Analyzing</span>
        </div>
      )}

      {isFailed && (
        <div className="status-badge failed">
          <span>Failed</span>
          <button
            className="retry-btn"
            onClick={handleRetryClick}
            title="Retry analysis"
          >
            <RefreshCw size={12} />
          </button>
        </div>
      )}

      {/* Favorite indicator */}
      {localFavorite && !isHovered && (
        <div className="favorite-indicator">
          <Heart size={14} fill="currentColor" />
        </div>
      )}

      {/* Tags on thumbnail */}
      {showTags && image.tags && image.tags.length > 0 && !isHovered && (
        <div className="thumbnail-tags">
          {image.tags.slice(0, 2).map(tag => (
            <span key={tag.id} className="thumbnail-tag">
              #{tag.name}
            </span>
          ))}
          {image.tags.length > 2 && (
            <span className="thumbnail-tag-more">+{image.tags.length - 2}</span>
          )}
        </div>
      )}

      {/* Filename bar - always visible when showFilename is enabled */}
      {showFilename && (
        <div className="filename-bar">
          <span className="thumbnail-filename">
            {image.display_name || image.filename}
          </span>
        </div>
      )}

      {/* Hover overlay with actions */}
      {isHovered && (
        <div className="thumbnail-overlay">
          {/* Top actions */}
          <div className="overlay-top">
            {isTrashView ? (
              <>
                <button
                  className="action-btn restore-btn"
                  onClick={handleRestoreClick}
                  title="Restore from trash"
                >
                  <RotateCcw size={16} />
                </button>
                <button
                  className="action-btn delete-btn permanent"
                  onClick={handlePermanentDeleteClick}
                  title="Delete permanently"
                >
                  <Trash2 size={16} />
                </button>
              </>
            ) : (
              <>
                {/* Retry button for failed images */}
                {isFailed && (
                  <button
                    className="action-btn retry-action-btn"
                    onClick={handleRetryClick}
                    title="Retry AI analysis"
                  >
                    <RefreshCw size={16} />
                  </button>
                )}
                <button
                  className={`action-btn favorite-btn ${localFavorite ? 'active' : ''}`}
                  onClick={handleFavoriteClick}
                  title={localFavorite ? 'Remove from favorites' : 'Add to favorites'}
                >
                  <Heart size={16} fill={localFavorite ? 'currentColor' : 'none'} />
                </button>
                <button
                  ref={albumBtnRef}
                  className="action-btn album-btn"
                  onClick={handleAlbumClick}
                  title="Add to album"
                >
                  <FolderPlus size={16} />
                </button>
                {showAlbumPicker && (
                  <AlbumPicker
                    imageIds={[image.id]}
                    onClose={handleCloseAlbumPicker}
                    anchorRect={albumBtnRect}
                  />
                )}
                <button
                  className="action-btn delete-btn"
                  onClick={handleDeleteClick}
                  title="Move to trash"
                >
                  <Trash2 size={16} />
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default React.memo(PhotoThumbnail);
