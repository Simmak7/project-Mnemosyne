import React from 'react';
import { FiSearch } from 'react-icons/fi';

/**
 * Search history display
 */
function SearchHistory({ searchHistory, onSelect }) {
  return (
    <div className="search-history">
      <h3 className="search-history-title">Recent Searches</h3>
      {searchHistory.length > 0 ? (
        <div className="search-history-list">
          {searchHistory.map((historyQuery, index) => (
            <button
              key={index}
              className="search-history-item"
              onClick={() => onSelect(historyQuery)}
            >
              <FiSearch className="history-icon" />
              <span>{historyQuery}</span>
            </button>
          ))}
        </div>
      ) : (
        <p className="search-history-empty">No recent searches</p>
      )}
      <div className="search-hint">
        <span>💡 Press Cmd/Ctrl+K to open search anywhere</span>
      </div>
    </div>
  );
}

export default SearchHistory;
