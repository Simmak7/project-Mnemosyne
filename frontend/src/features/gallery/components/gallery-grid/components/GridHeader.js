import React from 'react';

/**
 * Header for gallery grid showing view title and image count
 */
function GridHeader({
  isSearchMode,
  isAlbumView,
  currentAlbum,
  currentView,
  imageCount,
  hasFilter
}) {
  const getViewTitle = () => {
    if (isSearchMode) return 'Search Results';
    if (isAlbumView && currentAlbum) return currentAlbum.name;
    if (currentView === 'favorites') return 'Favorites';
    if (currentView === 'trash') return 'Trash';
    return 'All Photos';
  };

  return (
    <div className="gallery-grid-header">
      <div className="header-info">
        <h2 className="view-title">{getViewTitle()}</h2>
        <span className="image-count">
          {imageCount} {imageCount === 1 ? 'photo' : 'photos'}
          {hasFilter && ' (filtered)'}
        </span>
      </div>
    </div>
  );
}

export default GridHeader;
