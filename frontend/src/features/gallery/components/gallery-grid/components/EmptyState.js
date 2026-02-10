import React from 'react';

/**
 * Empty state for gallery grid
 */
function EmptyState({ isSearchMode, isAlbumView, currentAlbum, currentView }) {
  const getIcon = () => {
    if (isSearchMode) return '🔍';
    if (isAlbumView) return '📁';
    if (currentView === 'favorites') return '💛';
    if (currentView === 'trash') return '🗑️';
    return '📷';
  };

  const getTitle = () => {
    if (isSearchMode) return 'No results found';
    if (isAlbumView) return `${currentAlbum?.name || 'Album'} is empty`;
    if (currentView === 'favorites') return 'No favorites yet';
    if (currentView === 'trash') return 'Trash is empty';
    return 'No images yet';
  };

  const getDescription = () => {
    if (isSearchMode) return 'Try different keywords or switch search type';
    if (isAlbumView) return 'Add some images to this album';
    if (currentView === 'favorites') return 'Heart some images to see them here';
    if (currentView === 'trash') return 'Deleted images will appear here';
    return 'Upload some images to get started';
  };

  return (
    <div className="gallery-grid-empty">
      <div className="empty-icon">{getIcon()}</div>
      <h3>{getTitle()}</h3>
      <p>{getDescription()}</p>
    </div>
  );
}

export default EmptyState;
