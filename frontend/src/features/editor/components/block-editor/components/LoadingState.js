import React from 'react';

/**
 * Loading state for editor initialization
 */
function LoadingState() {
  return (
    <div className="ng-block-editor ng-block-editor-loading">
      <div className="loading-pulse"></div>
      <p>Initializing editor...</p>
    </div>
  );
}

export default LoadingState;
