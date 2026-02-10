import React from 'react';

/**
 * Loading state for gallery grid
 */
function LoadingState({ isLoading, dimensionsLoaded }) {
  if (!isLoading && dimensionsLoaded) return null;

  return (
    <div className="gallery-loading">
      <div className="loading-spinner" />
      <span>{isLoading ? 'Loading photos...' : 'Preparing layout...'}</span>
    </div>
  );
}

export default LoadingState;
