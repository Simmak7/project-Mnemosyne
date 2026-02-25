/**
 * FavoriteImagesWidget - Thumbnail grid of starred photos
 */
import React, { useState, useCallback } from 'react';
import { Heart } from 'lucide-react';
import WidgetShell from './WidgetShell';
import { API_URL } from '../../../utils/api';
import './FavoriteImagesWidget.css';

function Thumbnail({ image, onClick }) {
  const [loaded, setLoaded] = useState(false);
  const name = image.display_name || image.original_filename || 'Image';

  return (
    <div className="fav-image-thumb" onClick={() => onClick(image.id)}>
      <img
        src={`${API_URL}/image/${image.id}`}
        alt={name}
        loading="lazy"
        className={loaded ? 'loaded' : ''}
        onLoad={() => setLoaded(true)}
      />
      <span className="fav-image-name">{name}</span>
    </div>
  );
}

function FavoriteImagesWidget({ favoriteImages, isLoading, onNavigateToImage, onTabChange }) {
  const images = favoriteImages?.items || favoriteImages || [];

  const handleClick = useCallback((id) => {
    onNavigateToImage?.(id);
  }, [onNavigateToImage]);

  return (
    <WidgetShell
      icon={Heart}
      title="Favorite Images"
      action={images.length > 0 ? () => onTabChange?.('gallery') : undefined}
      actionLabel="View gallery"
      isLoading={isLoading}
    >
      {images.length > 0 ? (
        <div className="fav-images-grid">
          {images.slice(0, 8).map(img => (
            <Thumbnail key={img.id} image={img} onClick={handleClick} />
          ))}
        </div>
      ) : (
        <div className="fav-images-empty">
          <Heart size={24} className="widget-icon" />
          <p className="fav-images-empty-text">
            Star your favorite photos in the Gallery
          </p>
        </div>
      )}
    </WidgetShell>
  );
}

export default FavoriteImagesWidget;
