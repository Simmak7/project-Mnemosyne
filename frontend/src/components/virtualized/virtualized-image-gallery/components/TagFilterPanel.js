/**
 * TagFilterPanel - Filter images by tags
 */
import React from 'react';

function TagFilterPanel({ allTags, images, selectedTags, setSelectedTags }) {
  return (
    <div className="tag-filter-panel">
      <h4>Filter by Tags</h4>
      <div className="tag-filter-list">
        {allTags.map(tag => {
          const tagImageCount = images.filter(img =>
            img.tags?.some(t => t.id === tag.id)
          ).length;

          return (
            <label key={tag.id} className="tag-filter-item">
              <input
                type="checkbox"
                checked={selectedTags.includes(tag.id)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedTags([...selectedTags, tag.id]);
                  } else {
                    setSelectedTags(selectedTags.filter(id => id !== tag.id));
                  }
                }}
              />
              <span className="tag-name">#{tag.name}</span>
              <span className="tag-count">{tagImageCount}</span>
            </label>
          );
        })}
      </div>
      {selectedTags.length > 0 && (
        <button
          className="clear-filters-btn"
          onClick={() => setSelectedTags([])}
        >
          Clear All Filters
        </button>
      )}
    </div>
  );
}

export default TagFilterPanel;
