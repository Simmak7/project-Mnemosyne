import React from 'react';
import { RefreshCw } from 'lucide-react';
import './PullToRefreshIndicator.css';

/**
 * PullToRefreshIndicator - Visual feedback for pull-to-refresh.
 * Renders a glowing ring spinner in Neural Glass style.
 */
function PullToRefreshIndicator({ pullDistance, isRefreshing, progress }) {
  if (pullDistance === 0 && !isRefreshing) return null;

  return (
    <div
      className="ptr-indicator"
      style={{ height: `${pullDistance}px` }}
    >
      <div
        className={`ptr-spinner ${isRefreshing ? 'spinning' : ''}`}
        style={{
          opacity: Math.min(progress, 1),
          transform: `rotate(${progress * 360}deg) scale(${0.5 + progress * 0.5})`,
        }}
      >
        <RefreshCw size={20} />
      </div>
    </div>
  );
}

export default PullToRefreshIndicator;
