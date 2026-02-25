import React, { useState } from 'react';
import { ChevronUp, ChevronDown, Image, ExternalLink } from 'lucide-react';
import { API_URL as API_BASE } from '../../../utils/api';

/**
 * NoteMediaPreview - Collapsible image preview section
 */
function NoteMediaPreview({ imageIds, onHide, onImageClick }) {
  const [expanded, setExpanded] = useState(true);
  const [loadError, setLoadError] = useState({});

  if (!imageIds || imageIds.length === 0) return null;

  // Show first image as primary, rest as thumbnails
  const primaryImageId = imageIds[0];
  const otherImages = imageIds.slice(1, 4); // Show up to 3 more

  return (
    <div className={`note-media-preview ${expanded ? 'expanded' : 'collapsed'}`}>
      {/* Header with toggle */}
      <div className="media-header">
        <button className="media-toggle" onClick={() => setExpanded(!expanded)}>
          <Image size={14} />
          <span>Media Preview ({imageIds.length})</span>
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>
      </div>

      {/* Preview content */}
      {expanded && (
        <div className="media-content">
          {/* Primary image */}
          <div
            className="primary-image"
            onClick={() => onImageClick && onImageClick(primaryImageId)}
            role="button"
            tabIndex={0}
          >
            {loadError[primaryImageId] ? (
              <div className="image-error">
                <Image size={24} />
                <span>Failed to load</span>
              </div>
            ) : (
              <>
                <img
                  src={`${API_BASE}/image/${primaryImageId}`}
                  alt="Note attachment"
                  onError={() => setLoadError(prev => ({ ...prev, [primaryImageId]: true }))}
                />
                <div className="image-overlay">
                  <ExternalLink size={16} />
                  <span>View in Gallery</span>
                </div>
              </>
            )}
          </div>

          {/* Additional thumbnails */}
          {otherImages.length > 0 && (
            <div className="thumbnail-row">
              {otherImages.map(imageId => (
                <div
                  key={imageId}
                  className="thumbnail"
                  onClick={() => onImageClick && onImageClick(imageId)}
                  role="button"
                  tabIndex={0}
                >
                  {loadError[imageId] ? (
                    <div className="image-error">
                      <Image size={16} />
                    </div>
                  ) : (
                    <img
                      src={`${API_BASE}/image/${imageId}`}
                      alt="Note attachment"
                      onError={() => setLoadError(prev => ({ ...prev, [imageId]: true }))}
                    />
                  )}
                </div>
              ))}
              {imageIds.length > 4 && (
                <div className="thumbnail more-count">
                  +{imageIds.length - 4}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default NoteMediaPreview;
