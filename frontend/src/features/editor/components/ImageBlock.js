import React, { useState } from 'react';
import { Image, CheckCircle, AlertCircle, Tag, ExternalLink } from 'lucide-react';
import './ImageBlock.css';

/**
 * ImageBlock - Rich image embed component with metadata display
 * Renders images as beautiful cards with AI analysis info
 *
 * @param {Object} props
 * @param {string} props.src - Image source URL
 * @param {string} props.alt - Alt text for image
 * @param {string} props.imageId - Unique image identifier
 * @param {Object} props.metadata - Image metadata (dimensions, tags, analysis)
 * @param {Function} props.onClick - Click handler for image interaction
 * @param {Function} props.onTagClick - Handler for tag clicks
 */
function ImageBlock({
  src,
  alt = '',
  imageId,
  metadata = {},
  onClick,
  onTagClick,
}) {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  const {
    filename = 'image.jpg',
    width,
    height,
    analyzed = false,
    tags = [],
    description,
  } = metadata;

  const dimensions = width && height ? `${width}×${height}` : null;

  const handleImageLoad = () => {
    setImageLoaded(true);
  };

  const handleImageError = () => {
    setImageError(true);
  };

  const handleClick = () => {
    if (onClick) {
      onClick({ imageId, src, metadata });
    }
  };

  const handleTagClick = (tag, e) => {
    e.stopPropagation();
    if (onTagClick) {
      onTagClick(tag);
    }
  };

  return (
    <figure className="ng-image-block" onClick={handleClick}>
      {/* Image container */}
      <div className={`ng-image-block-preview ${imageLoaded ? 'loaded' : ''}`}>
        {!imageError ? (
          <>
            {!imageLoaded && (
              <div className="ng-image-block-placeholder">
                <Image size={32} className="placeholder-icon" />
              </div>
            )}
            <img
              src={src}
              alt={alt || filename}
              onLoad={handleImageLoad}
              onError={handleImageError}
              className={imageLoaded ? 'visible' : ''}
            />
          </>
        ) : (
          <div className="ng-image-block-error">
            <AlertCircle size={32} />
            <span>Failed to load image</span>
          </div>
        )}
      </div>

      {/* Metadata footer */}
      <figcaption className="ng-image-block-meta">
        <div className="ng-image-block-info">
          <span className="ng-image-block-filename">
            <Image size={14} />
            {filename}
          </span>

          {dimensions && (
            <span className="ng-image-block-dimensions">
              {dimensions}
            </span>
          )}

          <span className={`ng-image-block-status ${analyzed ? 'analyzed' : ''}`}>
            {analyzed ? (
              <>
                <CheckCircle size={14} />
                Analyzed
              </>
            ) : (
              <>
                <AlertCircle size={14} />
                Pending
              </>
            )}
          </span>
        </div>

        {/* Tags */}
        {tags.length > 0 && (
          <div className="ng-image-block-tags">
            {tags.map((tag, index) => (
              <button
                key={index}
                className="ng-image-block-tag"
                onClick={(e) => handleTagClick(tag, e)}
              >
                <Tag size={12} />
                {tag.name || tag}
              </button>
            ))}
          </div>
        )}

        {/* Description preview */}
        {description && (
          <p className="ng-image-block-description">{description}</p>
        )}
      </figcaption>

      {/* Expand indicator */}
      <button className="ng-image-block-expand" title="View details">
        <ExternalLink size={16} />
      </button>
    </figure>
  );
}

export default ImageBlock;
