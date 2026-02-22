/**
 * GalleryItem - Individual image card in the gallery
 */
import React from 'react';
import { Sparkles, RefreshCw, Trash2 } from 'lucide-react';
import LazyImage from '../../../layout/LazyImage';
import { API_URL } from '../../../../utils/api';

function GalleryItem({
  image,
  onOpenLightbox,
  onRetry,
  onDelete,
  retryingImages,
  deletingImages,
}) {
  return (
    <div className="gallery-item" onClick={() => onOpenLightbox(image)}>
      <div className="image-wrapper">
        <LazyImage
          src={`${API_URL}/image/${image.id}`}
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
                onRetry(image.id);
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
                onDelete(image.id, image.filename);
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
            onDelete(image.id, image.filename);
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
                    onRetry(image.id);
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
  );
}

export default GalleryItem;
