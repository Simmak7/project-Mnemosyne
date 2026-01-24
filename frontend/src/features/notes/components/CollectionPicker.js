import React, { useState, useRef, useEffect, useCallback } from 'react';
import { FolderPlus, Check, X, Plus } from 'lucide-react';
import { useCollections, useNoteCollections } from '../hooks/useCollections';
import './CollectionPicker.css';

/**
 * CollectionPicker - Dropdown to add/remove notes from collections
 * Uses fixed positioning to avoid overflow clipping issues
 */
function CollectionPicker({ noteId, onClose }) {
  const [isOpen, setIsOpen] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newCollectionName, setNewCollectionName] = useState('');
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0 });
  const buttonRef = useRef(null);
  const dropdownRef = useRef(null);

  const {
    collections,
    isLoading,
    createCollection,
    addNoteToCollection,
    removeNoteFromCollection,
    isCreating
  } = useCollections();

  const {
    collections: noteCollections,
    isLoading: isLoadingNoteCollections
  } = useNoteCollections(noteId);

  // Get set of collection IDs this note belongs to
  const noteCollectionIds = new Set(noteCollections.map(c => c.id));

  // Calculate dropdown position based on button location
  const updatePosition = useCallback(() => {
    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      const dropdownWidth = 240;
      const dropdownHeight = 320;

      // Position below the button, aligned to the right
      let left = rect.right - dropdownWidth;
      let top = rect.bottom + 8;

      // Make sure it doesn't go off-screen to the left
      if (left < 8) {
        left = 8;
      }

      // Make sure it doesn't go off-screen to the bottom
      if (top + dropdownHeight > window.innerHeight - 8) {
        // Position above the button instead
        top = rect.top - dropdownHeight - 8;
      }

      setDropdownPosition({ top, left });
    }
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target) &&
        buttonRef.current &&
        !buttonRef.current.contains(e.target)
      ) {
        setIsOpen(false);
        setShowCreateForm(false);
        if (onClose) onClose();
      }
    };

    const handleScroll = () => {
      if (isOpen) {
        updatePosition();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      window.addEventListener('scroll', handleScroll, true);
      window.addEventListener('resize', updatePosition);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
        window.removeEventListener('scroll', handleScroll, true);
        window.removeEventListener('resize', updatePosition);
      };
    }
  }, [isOpen, onClose, updatePosition]);

  const handleToggle = () => {
    if (!isOpen) {
      updatePosition();
      setShowCreateForm(false);
    }
    setIsOpen(!isOpen);
  };

  const handleCollectionClick = (collectionId) => {
    if (noteCollectionIds.has(collectionId)) {
      removeNoteFromCollection({ collectionId, noteId });
    } else {
      addNoteToCollection({ collectionId, noteId });
    }
  };

  const handleCreateSubmit = (e) => {
    e.preventDefault();
    if (newCollectionName.trim()) {
      createCollection(
        { name: newCollectionName.trim() },
        {
          onSuccess: (newCollection) => {
            // Add note to newly created collection
            if (newCollection?.id) {
              addNoteToCollection({ collectionId: newCollection.id, noteId });
            }
            setNewCollectionName('');
            setShowCreateForm(false);
          }
        }
      );
    }
  };

  return (
    <div className="collection-picker">
      <button
        ref={buttonRef}
        className="action-btn"
        onClick={handleToggle}
        title="Add to collection"
      >
        <FolderPlus size={16} />
      </button>

      {isOpen && (
        <div
          ref={dropdownRef}
          className="collection-picker-dropdown"
          style={{
            position: 'fixed',
            top: dropdownPosition.top,
            left: dropdownPosition.left,
          }}
        >
          <div className="dropdown-header">
            <span>Add to Collection</span>
            {noteCollectionIds.size > 0 && (
              <span className="in-collections-count">
                In {noteCollectionIds.size}
              </span>
            )}
          </div>

          <div className="dropdown-content">
            {isLoading || isLoadingNoteCollections ? (
              <div className="dropdown-loading">Loading...</div>
            ) : collections.length === 0 ? (
              <div className="dropdown-empty">No collections yet</div>
            ) : (
              <div className="collection-list">
                {collections.map((collection) => {
                  const isInCollection = noteCollectionIds.has(collection.id);
                  return (
                    <button
                      key={collection.id}
                      className={`collection-option ${isInCollection ? 'active' : ''}`}
                      onClick={() => handleCollectionClick(collection.id)}
                    >
                      <span className="collection-option-icon">
                        {collection.icon || '📁'}
                      </span>
                      <span className="collection-option-name">
                        {collection.name}
                      </span>
                      {isInCollection && (
                        <Check size={14} className="check-icon" />
                      )}
                    </button>
                  );
                })}
              </div>
            )}

            {/* Create new collection */}
            {showCreateForm ? (
              <form className="create-inline-form" onSubmit={handleCreateSubmit}>
                <input
                  type="text"
                  value={newCollectionName}
                  onChange={(e) => setNewCollectionName(e.target.value)}
                  placeholder="New collection..."
                  autoFocus
                  className="create-inline-input"
                />
                <button
                  type="submit"
                  className="create-inline-btn confirm"
                  disabled={!newCollectionName.trim() || isCreating}
                >
                  <Check size={14} />
                </button>
                <button
                  type="button"
                  className="create-inline-btn cancel"
                  onClick={() => {
                    setShowCreateForm(false);
                    setNewCollectionName('');
                  }}
                >
                  <X size={14} />
                </button>
              </form>
            ) : (
              <button
                className="create-new-btn"
                onClick={() => setShowCreateForm(true)}
              >
                <Plus size={14} />
                <span>New Collection</span>
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default CollectionPicker;
