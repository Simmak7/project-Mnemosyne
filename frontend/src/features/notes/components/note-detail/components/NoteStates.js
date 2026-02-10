import React from 'react';

/**
 * Empty state when no note is selected
 */
export function EmptyState() {
  return (
    <div className="note-detail note-detail-empty">
      <div className="empty-state">
        <span className="empty-icon">📄</span>
        <h3>Select a note</h3>
        <p>Choose a note from the list to view its contents</p>
      </div>
    </div>
  );
}

/**
 * Loading state skeleton
 */
export function LoadingState() {
  return (
    <div className="note-detail note-detail-loading">
      <div className="loading-skeleton">
        <div className="skeleton-header">
          <div className="skeleton-title" />
          <div className="skeleton-meta" />
        </div>
        <div className="skeleton-tabs" />
        <div className="skeleton-content">
          <div className="skeleton-line" />
          <div className="skeleton-line" />
          <div className="skeleton-line short" />
        </div>
      </div>
    </div>
  );
}

/**
 * Error state
 */
export function ErrorState({ error }) {
  return (
    <div className="note-detail note-detail-error">
      <div className="error-state">
        <span className="error-icon">⚠️</span>
        <h3>Failed to load note</h3>
        <p>{error}</p>
      </div>
    </div>
  );
}
