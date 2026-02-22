import React, { useState, useEffect } from 'react';
import Select from 'react-select';
import { FiTag, FiX } from 'react-icons/fi';
import { API_URL } from '../../utils/api';
import './TagSelector.css';

/**
 * Tag selector with multi-select and counts
 *
 * Features:
 * - Multi-select dropdown with search
 * - Show note count per tag
 * - Create new tags inline (press Enter)
 * - Recently used tags at top
 * - Tag chips with remove button
 */
function TagSelector({ selectedTags = [], onChange }) {
  const [allTags, setAllTags] = useState([]);
  const [loading, setLoading] = useState(false);
  const [inputValue, setInputValue] = useState('');

  // Fetch all tags with counts
  useEffect(() => {
    const fetchTags = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_URL}/tags/`, {
          headers: { 'Authorization': `Bearer ${token}` },
        });

        if (response.ok) {
          const tags = await response.json();
          setAllTags(tags);
        }
      } catch (error) {
        console.error('Error fetching tags:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTags();
  }, []);

  // Convert tags to react-select format
  const tagOptions = allTags.map((tag) => ({
    value: tag.id,
    label: tag.name,
    noteCount: tag.note_count || 0,
    tag,
  }));

  // Convert selected tags to react-select format
  const selectedOptions = selectedTags.map((tag) => {
    if (typeof tag === 'string') {
      return {
        value: tag,
        label: tag,
        noteCount: 0,
        isNew: true,
      };
    }
    return {
      value: tag.id,
      label: tag.name,
      noteCount: tag.note_count || 0,
      tag,
    };
  });

  // Handle tag selection
  const handleChange = (selected) => {
    const tags = selected ? selected.map((opt) => {
      if (opt.isNew) {
        return opt.label; // New tag as string
      }
      return opt.tag; // Existing tag object
    }) : [];
    onChange(tags);
  };

  // Handle creating new tag
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && inputValue) {
      e.preventDefault();
      const newTag = inputValue.trim();

      // Check if tag already exists
      const exists = selectedTags.some((tag) =>
        typeof tag === 'string' ? tag === newTag : tag.name === newTag
      );

      if (!exists && newTag) {
        onChange([...selectedTags, newTag]);
        setInputValue('');
      }
    }
  };

  // Custom option component to show note count
  const formatOptionLabel = ({ label, noteCount }) => (
    <div className="tag-option">
      <span className="tag-option-label">{label}</span>
      {noteCount > 0 && (
        <span className="tag-option-count">{noteCount} note{noteCount !== 1 ? 's' : ''}</span>
      )}
    </div>
  );

  // Custom styles for react-select
  const customStyles = {
    control: (provided, state) => ({
      ...provided,
      borderColor: state.isFocused ? '#4A90E2' : '#ddd',
      boxShadow: state.isFocused ? '0 0 0 1px #4A90E2' : 'none',
      '&:hover': {
        borderColor: '#4A90E2',
      },
    }),
    multiValue: (provided) => ({
      ...provided,
      backgroundColor: '#E8F4FD',
      borderRadius: '12px',
    }),
    multiValueLabel: (provided) => ({
      ...provided,
      color: '#2C5AA0',
      fontWeight: 500,
    }),
    multiValueRemove: (provided) => ({
      ...provided,
      color: '#2C5AA0',
      '&:hover': {
        backgroundColor: '#D0E8FA',
        color: '#1A4B8F',
      },
    }),
  };

  return (
    <div className="tag-selector-container">
      <div className="tag-selector-header">
        <FiTag className="tag-icon" />
        <span className="tag-label">Tags</span>
      </div>

      <Select
        isMulti
        value={selectedOptions}
        onChange={handleChange}
        options={tagOptions}
        formatOptionLabel={formatOptionLabel}
        placeholder="Search or create tags..."
        isLoading={loading}
        isClearable={false}
        styles={customStyles}
        inputValue={inputValue}
        onInputChange={setInputValue}
        onKeyDown={handleKeyDown}
        noOptionsMessage={() => inputValue ? `Press Enter to create "${inputValue}"` : 'No tags yet'}
        className="tag-select"
        classNamePrefix="tag-select"
      />

      {selectedTags.length === 0 && (
        <div className="tag-selector-hint">
          <span>💡 Type to search existing tags or create new ones</span>
        </div>
      )}

      {/* Alternative tag chips display (optional) */}
      {selectedTags.length > 0 && (
        <div className="tag-chips-container">
          {selectedTags.map((tag, index) => {
            const tagName = typeof tag === 'string' ? tag : tag.name;
            return (
              <div key={index} className="tag-chip">
                <FiTag className="tag-chip-icon" />
                <span className="tag-chip-label">{tagName}</span>
                <button
                  className="tag-chip-remove"
                  onClick={() => {
                    const newTags = selectedTags.filter((_, i) => i !== index);
                    onChange(newTags);
                  }}
                  aria-label={`Remove ${tagName}`}
                >
                  <FiX />
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default TagSelector;
