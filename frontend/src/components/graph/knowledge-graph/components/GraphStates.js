import React from 'react';
import { HelpCircle } from 'lucide-react';

/**
 * Loading state for knowledge graph
 */
export function LoadingState() {
  return (
    <div className="knowledge-graph-container">
      <div className="graph-loading">
        <div className="loading-spinner"></div>
        <p>Loading knowledge graph...</p>
      </div>
    </div>
  );
}

/**
 * Error state for knowledge graph
 */
export function ErrorState({ error, onRetry }) {
  return (
    <div className="knowledge-graph-container">
      <div className="graph-error">
        <div className="error-icon">⚠️</div>
        <h3>Failed to load graph</h3>
        <p>{error}</p>
        <button onClick={onRetry} className="retry-button">
          Retry
        </button>
      </div>
    </div>
  );
}

/**
 * Empty state for knowledge graph
 */
export function EmptyState({ onShowHelp }) {
  return (
    <div className="graph-empty-state">
      <div className="empty-icon">🕸️</div>
      <h3>No graph data</h3>
      <p>Create notes with wikilinks and tags to build your knowledge graph!</p>
      <button onClick={onShowHelp} className="empty-help-btn">
        <HelpCircle className="w-5 h-5" />
        Learn How to Build Your Graph
      </button>
    </div>
  );
}
