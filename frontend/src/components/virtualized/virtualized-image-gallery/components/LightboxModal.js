/**
 * LightboxModal - Full image view with details
 */
import React, { useEffect, useCallback } from 'react';
import { RefreshCw } from 'lucide-react';

function LightboxModal({
  image,
  onClose,
  onRetry,
  onViewNote,
  retryingImages,
}) {
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') {
      onClose();
    }
  }, [onClose]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'auto';
    };
  }, [handleKeyDown]);

  if (!image) return null;

  return (
    <div className="lightbox-overlay" onClick={onClose}>
      <div className="lightbox-content" onClick={(e) => e.stopPropagation()}>
        <button
          className="lightbox-close"
          onClick={onClose}
          aria-label="Close lightbox"
        >
          &times;
        </button>
        <div className="lightbox-image-container">
          <img
            src={`http://localhost:8000/image/${image.id}`}
            alt={image.filename}
            className="lightbox-image"
          />
        </div>
        <div className="lightbox-info">
          <h3>{image.filename}</h3>
          <div className="lightbox-meta">
            <div className="lightbox-meta-row">
              <span className="lightbox-meta-label">Status:</span>
              <span className={`status-badge ${image.ai_analysis_status}`}>
                {image.ai_analysis_status}
              </span>
            </div>

            <div className="lightbox-meta-row">
              <span className="lightbox-meta-label">Uploaded:</span>
              <span className="lightbox-meta-value">
                {new Date(image.uploaded_at).toLocaleString(undefined, {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </span>
            </div>

            {image.prompt && (
              <div className="lightbox-meta-row lightbox-prompt-row">
                <span className="lightbox-meta-label">Prompt:</span>
                <span className="lightbox-meta-value">{image.prompt}</span>
              </div>
            )}

            {image.tags && image.tags.length > 0 && (
              <div className="lightbox-meta-row lightbox-tags-row">
                <span className="lightbox-meta-label">Tags:</span>
                <div className="lightbox-tags">
                  {image.tags.map(tag => (
                    <span key={tag.id} className="lightbox-tag">
                      #{tag.name}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {image.ai_analysis_status === 'failed' && (
              <div className="lightbox-retry-section">
                <button
                  className="retry-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    onRetry(image.id);
                  }}
                  disabled={retryingImages.has(image.id)}
                >
                  <RefreshCw size={14} className={retryingImages.has(image.id) ? 'retry-spinning' : ''} />
                  {retryingImages.has(image.id) ? 'Retrying...' : 'Retry Analysis'}
                </button>
              </div>
            )}

            {/* Display Notes */}
            {image.notes && image.notes.filter(Boolean).length > 0 && (
              <div className="lightbox-notes-section">
                <div className="lightbox-meta-label" style={{ marginTop: '1rem', marginBottom: '0.5rem' }}>
                  Generated Notes ({image.notes.filter(Boolean).length}):
                </div>
                {image.notes.filter(Boolean).map(note => {
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
                            onClose();
                          }
                        }}
                      >
                        View Full Note &rarr;
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
  );
}

export default LightboxModal;
