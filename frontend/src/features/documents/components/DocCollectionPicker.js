import React, { useState, useRef, useEffect, useCallback } from 'react';
import ReactDOM from 'react-dom';
import { FolderPlus, Check, X, Plus } from 'lucide-react';
import { useDocCollections, useDocCollectionsForDocument } from '../hooks/useDocumentCollections';
import './DocCollectionPicker.css';

/**
 * DocCollectionPicker - Dropdown to add/remove documents from collections
 * Uses fixed positioning via portal to avoid overflow clipping
 */
function DocCollectionPicker({ documentId, onClose }) {
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
    addDocumentToCollection,
    removeDocumentFromCollection,
    isCreating
  } = useDocCollections();

  const {
    collections: docCollections,
    isLoading: isLoadingDocCollections
  } = useDocCollectionsForDocument(documentId);

  const docCollectionIds = new Set(docCollections.map(c => c.id));

  const updatePosition = useCallback(() => {
    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      const dropdownWidth = 240;
      const dropdownHeight = 320;

      let left = rect.right - dropdownWidth;
      let top = rect.bottom + 8;

      if (left < 8) left = 8;
      if (top + dropdownHeight > window.innerHeight - 8) {
        top = rect.top - dropdownHeight - 8;
      }

      setDropdownPosition({ top, left });
    }
  }, []);

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
      if (isOpen) updatePosition();
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
    if (docCollectionIds.has(collectionId)) {
      removeDocumentFromCollection({ collectionId, documentId });
    } else {
      addDocumentToCollection({ collectionId, documentId });
    }
  };

  const handleCreateSubmit = (e) => {
    e.preventDefault();
    if (newCollectionName.trim()) {
      createCollection(
        { name: newCollectionName.trim() },
        {
          onSuccess: (newCollection) => {
            if (newCollection?.id) {
              addDocumentToCollection({ collectionId: newCollection.id, documentId });
            }
            setNewCollectionName('');
            setShowCreateForm(false);
          }
        }
      );
    }
  };

  return (
    <div className="doc-collection-picker">
      <button
        ref={buttonRef}
        className="review-header-action"
        onClick={handleToggle}
        title="Add to collection"
      >
        <FolderPlus size={16} />
      </button>

      {isOpen && ReactDOM.createPortal(
        <div
          ref={dropdownRef}
          className="doc-collection-picker-dropdown"
          style={{
            position: 'fixed',
            top: dropdownPosition.top,
            left: dropdownPosition.left,
          }}
        >
          <div className="doc-picker-header">
            <span>Add to Collection</span>
            <div className="doc-picker-header-right">
              {docCollectionIds.size > 0 && (
                <span className="doc-picker-in-count">
                  In {docCollectionIds.size}
                </span>
              )}
              <button
                className="doc-picker-close-btn"
                onClick={() => {
                  setIsOpen(false);
                  setShowCreateForm(false);
                  if (onClose) onClose();
                }}
                title="Done"
              >
                <X size={14} />
              </button>
            </div>
          </div>

          <div className="doc-picker-content">
            {isLoading || isLoadingDocCollections ? (
              <div className="doc-picker-loading">Loading...</div>
            ) : collections.length === 0 ? (
              <div className="doc-picker-empty">No collections yet</div>
            ) : (
              <div className="doc-picker-list">
                {collections.map((collection) => {
                  const isIn = docCollectionIds.has(collection.id);
                  return (
                    <button
                      key={collection.id}
                      className={`doc-picker-option ${isIn ? 'active' : ''}`}
                      onClick={() => handleCollectionClick(collection.id)}
                    >
                      <span className="doc-picker-option-icon">
                        {collection.icon || '\uD83D\uDCC1'}
                      </span>
                      <span className="doc-picker-option-name">
                        {collection.name}
                      </span>
                      {isIn && <Check size={14} className="doc-picker-check" />}
                    </button>
                  );
                })}
              </div>
            )}

            {showCreateForm ? (
              <form className="doc-picker-create-form" onSubmit={handleCreateSubmit}>
                <input
                  type="text"
                  value={newCollectionName}
                  onChange={(e) => setNewCollectionName(e.target.value)}
                  placeholder="New collection..."
                  autoFocus
                  className="doc-picker-create-input"
                />
                <button
                  type="submit"
                  className="doc-picker-create-btn confirm"
                  disabled={!newCollectionName.trim() || isCreating}
                >
                  <Check size={14} />
                </button>
                <button
                  type="button"
                  className="doc-picker-create-btn cancel"
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
                className="doc-picker-new-btn"
                onClick={() => setShowCreateForm(true)}
              >
                <Plus size={14} />
                <span>New Collection</span>
              </button>
            )}
          </div>

          <div className="doc-picker-footer">
            <button
              className="doc-picker-done-btn"
              onClick={() => {
                setIsOpen(false);
                setShowCreateForm(false);
                if (onClose) onClose();
              }}
            >
              Done
            </button>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}

export default DocCollectionPicker;
