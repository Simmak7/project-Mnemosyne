import React, { useRef } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { FiFileText, FiTag, FiImage, FiCalendar } from 'react-icons/fi';
import { format } from 'date-fns';
import './SearchResults.css';

/**
 * Virtualized search results list
 *
 * Features:
 * - Virtual scrolling for performance
 * - Mixed result types (notes, tags, images)
 * - Result highlighting
 * - Click to open/navigate
 * - Empty state
 */
function SearchResults({ results, loading, query, onClose, onResultClick }) {
  const parentRef = useRef(null);

  // Virtualizer setup
  const virtualizer = useVirtualizer({
    count: results.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80,
    overscan: 5,
  });

  // Determine result type
  const getResultType = (result) => {
    if (result.filename) return 'image';
    if (result.name && !result.content) return 'tag';
    return 'note';
  };

  // Get result icon
  const getResultIcon = (type) => {
    switch (type) {
      case 'note':
        return <FiFileText className="result-icon note-icon" />;
      case 'tag':
        return <FiTag className="result-icon tag-icon" />;
      case 'image':
        return <FiImage className="result-icon image-icon" />;
      default:
        return <FiFileText className="result-icon" />;
    }
  };

  // Get result title
  const getResultTitle = (result, type) => {
    if (type === 'note') return result.title;
    if (type === 'tag') return `#${result.name}`;
    if (type === 'image') return result.filename;
    return 'Untitled';
  };

  // Get result snippet
  const getResultSnippet = (result, type) => {
    if (type === 'note') {
      const content = result.content || '';
      return content.substring(0, 150) + (content.length > 150 ? '...' : '');
    }
    if (type === 'tag') {
      const noteCount = result.note_count || 0;
      return `Used in ${noteCount} note${noteCount !== 1 ? 's' : ''}`;
    }
    if (type === 'image') {
      return result.ai_analysis_status === 'completed'
        ? 'Analysis complete'
        : result.ai_analysis_status || 'Pending analysis';
    }
    return '';
  };

  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return '';
    try {
      return format(new Date(dateString), 'MMM dd, yyyy');
    } catch {
      return '';
    }
  };

  // Highlight query in text
  const highlightText = (text, query) => {
    if (!query || !text) return text;

    const parts = text.split(new RegExp(`(${query})`, 'gi'));
    return parts.map((part, index) =>
      part.toLowerCase() === query.toLowerCase() ? (
        <mark key={index} className="search-highlight">
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  // Handle result click
  const handleResultClick = (result, type) => {
    console.log('Result clicked:', type, result.id);

    // Call the parent's onResultClick handler with query for highlighting
    if (onResultClick) {
      onResultClick(result, query);
    }

    // Close search
    if (onClose) onClose();
  };

  if (loading) {
    return (
      <div className="search-results-container">
        <div className="search-loading">
          <div className="loading-spinner"></div>
          <span>Searching...</span>
        </div>
      </div>
    );
  }

  if (results.length === 0 && query) {
    return (
      <div className="search-results-container">
        <div className="search-empty">
          <div className="empty-icon">🔍</div>
          <h3>No results found</h3>
          <p>Try different keywords or adjust your filters</p>
        </div>
      </div>
    );
  }

  return (
    <div className="search-results-container">
      <div className="search-results-header">
        <span className="results-count">
          {results.length} result{results.length !== 1 ? 's' : ''}
        </span>
      </div>

      <div ref={parentRef} className="search-results-scroll">
        <div
          style={{
            height: `${virtualizer.getTotalSize()}px`,
            width: '100%',
            position: 'relative',
          }}
        >
          {virtualizer.getVirtualItems().map((virtualItem) => {
            const result = results[virtualItem.index];
            const type = getResultType(result);
            const title = getResultTitle(result, type);
            const snippet = getResultSnippet(result, type);
            const date = result.created_at || result.uploaded_at;

            return (
              <div
                key={virtualItem.key}
                data-index={virtualItem.index}
                ref={virtualizer.measureElement}
                className="virtual-result-item"
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  transform: `translateY(${virtualItem.start}px)`,
                }}
                onClick={() => handleResultClick(result, type)}
              >
                <div className="result-card">
                  <div className="result-header">
                    {getResultIcon(type)}
                    <div className="result-title-section">
                      <h4 className="result-title">
                        {highlightText(title, query)}
                      </h4>
                      <span className="result-type-badge">{type}</span>
                    </div>
                  </div>

                  {snippet && (
                    <p className="result-snippet">
                      {highlightText(snippet, query)}
                    </p>
                  )}

                  <div className="result-footer">
                    {date && (
                      <span className="result-date">
                        <FiCalendar className="date-icon" />
                        {formatDate(date)}
                      </span>
                    )}

                    {result.tags && result.tags.length > 0 && (
                      <div className="result-tags">
                        {result.tags.slice(0, 3).map((tag, idx) => (
                          <span key={idx} className="result-tag">
                            {typeof tag === 'string' ? tag : tag.name}
                          </span>
                        ))}
                        {result.tags.length > 3 && (
                          <span className="result-tag-more">
                            +{result.tags.length - 3}
                          </span>
                        )}
                      </div>
                    )}

                    {result.score && (
                      <span className="result-score">
                        Score: {(result.score * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default SearchResults;
