import React from 'react';
import { Hash, ChevronRight, ChevronDown } from 'lucide-react';

/**
 * Smart tags section
 */
function SmartTagsSection({
  tagsExpanded,
  setTagsExpanded,
  smartTags,
  selectedTagFilter,
  onTagClick,
}) {
  return (
    <div className="sidebar-section">
      <button
        className="section-header"
        onClick={() => setTagsExpanded(!tagsExpanded)}
      >
        {tagsExpanded ? (
          <ChevronDown size={16} className="section-chevron" />
        ) : (
          <ChevronRight size={16} className="section-chevron" />
        )}
        <Hash size={16} className="section-icon" />
        <span className="section-title">Smart Tags</span>
        <span className="section-count">{smartTags.length}</span>
      </button>

      {tagsExpanded && (
        <div className="tags-list">
          {smartTags.length === 0 ? (
            <div className="tags-empty">
              <p>No tags yet</p>
            </div>
          ) : (
            smartTags.map((tag) => (
              <button
                key={tag.name}
                className={`tag-item ${selectedTagFilter === tag.name ? 'active' : ''}`}
                onClick={() => onTagClick(tag.name)}
              >
                <span className="tag-hash">#</span>
                <span className="tag-name">{tag.name}</span>
                <span className="tag-count">{tag.count}</span>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}

export default SmartTagsSection;
