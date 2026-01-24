import React, { useMemo, useState } from 'react';
import {
  ArrowUpDown,
  Calendar,
  Type,
  HardDrive,
  ChevronUp,
  ChevronDown,
  Tag,
  X,
  SlidersHorizontal,
  Eye,
  EyeOff,
  Search
} from 'lucide-react';
import { useGalleryTags, useGalleryImages } from '../hooks/useGalleryImages';
import './GalleryContextPanel.css';

/**
 * GalleryContextPanel - Right panel with sort, view options, and tag filters
 */
function GalleryContextPanel({
  selectedTags,
  onTagsChange,
  sortBy,
  sortOrder,
  onSortChange,
  rowHeight,
  onRowHeightChange,
  showFilenames,
  onShowFilenamesChange,
  showDateHeaders,
  onShowDateHeadersChange,
  showTags,
  onShowTagsChange
}) {
  const { tags, isLoading: tagsLoading } = useGalleryTags();
  const { images } = useGalleryImages({ view: 'all' });

  // Tag search state
  const [tagSearch, setTagSearch] = useState('');

  // Calculate tag counts from current images
  const tagCounts = useMemo(() => {
    const counts = {};
    images.forEach(img => {
      img.tags?.forEach(tag => {
        counts[tag.id] = (counts[tag.id] || 0) + 1;
      });
    });
    return counts;
  }, [images]);

  // Sort tags by usage count (most used first), then alphabetically
  const sortedTags = useMemo(() => {
    return [...tags].sort((a, b) => {
      const countA = tagCounts[a.id] || 0;
      const countB = tagCounts[b.id] || 0;
      // Primary sort: by count (descending)
      if (countB !== countA) return countB - countA;
      // Secondary sort: alphabetically
      return a.name.localeCompare(b.name);
    });
  }, [tags, tagCounts]);

  // Filter tags by search term
  const filteredTags = useMemo(() => {
    if (!tagSearch.trim()) return sortedTags;
    const searchLower = tagSearch.toLowerCase().trim();
    return sortedTags.filter(tag =>
      tag.name.toLowerCase().includes(searchLower)
    );
  }, [sortedTags, tagSearch]);

  // Clear tag search
  const clearTagSearch = () => {
    setTagSearch('');
  };

  // Sort options
  const sortOptions = [
    { id: 'date', label: 'Date', icon: Calendar },
    { id: 'name', label: 'Name', icon: Type },
    { id: 'size', label: 'Size', icon: HardDrive }
  ];

  const handleSortClick = (field) => {
    if (sortBy === field) {
      // Toggle order if same field
      onSortChange(field, sortOrder === 'desc' ? 'asc' : 'desc');
    } else {
      // Default to descending for new field
      onSortChange(field, 'desc');
    }
  };

  const handleTagToggle = (tagId) => {
    if (selectedTags.includes(tagId)) {
      onTagsChange(selectedTags.filter(id => id !== tagId));
    } else {
      onTagsChange([...selectedTags, tagId]);
    }
  };

  const clearAllTags = () => {
    onTagsChange([]);
  };

  return (
    <div className="gallery-context-panel">
      {/* Sort Section */}
      <div className="context-section">
        <div className="section-header">
          <ArrowUpDown size={14} />
          <span>Sort By</span>
        </div>
        <div className="sort-options">
          {sortOptions.map((option) => {
            const Icon = option.icon;
            const isActive = sortBy === option.id;

            return (
              <button
                key={option.id}
                className={`sort-option ${isActive ? 'active' : ''}`}
                onClick={() => handleSortClick(option.id)}
              >
                <Icon size={14} />
                <span>{option.label}</span>
                {isActive && (
                  sortOrder === 'desc' ? (
                    <ChevronDown size={14} className="sort-direction" />
                  ) : (
                    <ChevronUp size={14} className="sort-direction" />
                  )
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* View Options Section */}
      <div className="context-section">
        <div className="section-header">
          <SlidersHorizontal size={14} />
          <span>View Options</span>
        </div>

        <div className="view-options">
          {/* Row Height Slider */}
          <div className="option-row">
            <label htmlFor="row-height">Thumbnail Size</label>
            <div className="slider-container">
              <span className="slider-value">{rowHeight}px</span>
              <input
                type="range"
                id="row-height"
                min="120"
                max="300"
                step="20"
                value={rowHeight}
                onChange={(e) => onRowHeightChange(Number(e.target.value))}
                className="slider"
              />
            </div>
          </div>

          {/* Toggle Options */}
          <button
            className={`toggle-option ${showFilenames ? 'active' : ''}`}
            onClick={() => onShowFilenamesChange(!showFilenames)}
          >
            {showFilenames ? <Eye size={14} /> : <EyeOff size={14} />}
            <span>Show Filenames</span>
          </button>

          <button
            className={`toggle-option ${showDateHeaders ? 'active' : ''}`}
            onClick={() => onShowDateHeadersChange(!showDateHeaders)}
          >
            <Calendar size={14} />
            <span>Date Headers</span>
          </button>

          <button
            className={`toggle-option ${showTags ? 'active' : ''}`}
            onClick={() => onShowTagsChange(!showTags)}
          >
            <Tag size={14} />
            <span>Show Tags</span>
          </button>
        </div>
      </div>

      {/* Tags Filter Section */}
      <div className="context-section tags-section">
        <div className="section-header">
          <Tag size={14} />
          <span>Filter by Tags</span>
          {selectedTags.length > 0 && (
            <button className="clear-tags-btn" onClick={clearAllTags}>
              <X size={12} />
              Clear
            </button>
          )}
        </div>

        {/* Tag Search Input */}
        <div className="tag-search-container">
          <Search size={14} className="tag-search-icon" />
          <input
            type="text"
            className="tag-search-input"
            placeholder="Search tags..."
            value={tagSearch}
            onChange={(e) => setTagSearch(e.target.value)}
          />
          {tagSearch && (
            <button className="tag-search-clear" onClick={clearTagSearch}>
              <X size={14} />
            </button>
          )}
        </div>

        <div className="tags-list">
          {tagsLoading ? (
            <div className="tags-loading">Loading tags...</div>
          ) : filteredTags.length === 0 ? (
            tagSearch ? (
              <div className="tags-empty">No tags matching "{tagSearch}"</div>
            ) : (
              <div className="tags-empty">No tags found</div>
            )
          ) : (
            filteredTags.map((tag) => {
              const isSelected = selectedTags.includes(tag.id);
              const count = tagCounts[tag.id] || 0;

              return (
                <button
                  key={tag.id}
                  className={`tag-pill ${isSelected ? 'active' : ''} ${count === 0 ? 'unused' : ''}`}
                  onClick={() => handleTagToggle(tag.id)}
                  title={`${tag.name}: ${count} photo${count !== 1 ? 's' : ''}`}
                >
                  <span className="tag-name">#{tag.name}</span>
                  <span className="tag-count">{count}</span>
                </button>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}

export default GalleryContextPanel;
