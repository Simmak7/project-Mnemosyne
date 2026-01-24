/**
 * AlbumSelector - Dropdown for selecting album to add images after upload
 * Reuses the useAlbums hook from gallery feature
 */

import React, { useState, useRef, useEffect } from 'react';
import { FolderPlus, Check, Plus, X, ChevronDown } from 'lucide-react';
import { useAlbums } from '../../gallery/hooks/useAlbums';

import './AlbumSelector.css';

/**
 * AlbumSelector Component
 * @param {object} props
 * @param {number|null} props.selectedAlbumId - Currently selected album ID
 * @param {function} props.onAlbumChange - Callback when album selection changes
 */
function AlbumSelector({ selectedAlbumId, onAlbumChange }) {
  const [isOpen, setIsOpen] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newAlbumName, setNewAlbumName] = useState('');
  const dropdownRef = useRef(null);

  const {
    albums,
    isLoading,
    createAlbum,
    isCreating
  } = useAlbums();

  // Find selected album
  const selectedAlbum = albums.find(a => a.id === selectedAlbumId);

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false);
        setShowCreateForm(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Handle creating new album
  const handleCreateAlbum = (e) => {
    e.preventDefault();
    if (newAlbumName.trim()) {
      createAlbum(
        { name: newAlbumName.trim() },
        {
          onSuccess: (newAlbum) => {
            if (newAlbum?.id) {
              onAlbumChange(newAlbum.id);
            }
            setNewAlbumName('');
            setShowCreateForm(false);
            setIsOpen(false);
          }
        }
      );
    }
  };

  // Handle selecting album
  const handleSelectAlbum = (albumId) => {
    onAlbumChange(albumId);
    setIsOpen(false);
  };

  // Handle clearing selection
  const handleClear = (e) => {
    e.stopPropagation();
    onAlbumChange(null);
  };

  return (
    <div className="album-selector" ref={dropdownRef}>
      {/* Trigger button */}
      <button
        className={`album-selector-trigger ${selectedAlbum ? 'has-selection' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        type="button"
      >
        <FolderPlus size={14} />
        <span className="album-selector-label">
          {selectedAlbum ? selectedAlbum.name : 'None selected'}
        </span>
        {selectedAlbum ? (
          <button
            className="album-selector-clear"
            onClick={handleClear}
            title="Clear selection"
          >
            <X size={12} />
          </button>
        ) : (
          <ChevronDown size={14} className={isOpen ? 'rotated' : ''} />
        )}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="album-selector-dropdown">
          {isLoading ? (
            <div className="album-selector-loading">Loading...</div>
          ) : (
            <>
              {/* Create new album */}
              {showCreateForm ? (
                <form className="album-selector-create" onSubmit={handleCreateAlbum}>
                  <input
                    type="text"
                    value={newAlbumName}
                    onChange={(e) => setNewAlbumName(e.target.value)}
                    placeholder="New album name..."
                    autoFocus
                    className="album-selector-input"
                  />
                  <button
                    type="submit"
                    className="album-selector-btn confirm"
                    disabled={!newAlbumName.trim() || isCreating}
                  >
                    <Check size={12} />
                  </button>
                  <button
                    type="button"
                    className="album-selector-btn cancel"
                    onClick={() => {
                      setShowCreateForm(false);
                      setNewAlbumName('');
                    }}
                  >
                    <X size={12} />
                  </button>
                </form>
              ) : (
                <button
                  className="album-selector-item create-new"
                  onClick={() => setShowCreateForm(true)}
                >
                  <Plus size={14} />
                  <span>Create new album</span>
                </button>
              )}

              {/* None option */}
              <button
                className={`album-selector-item ${!selectedAlbumId ? 'selected' : ''}`}
                onClick={() => handleSelectAlbum(null)}
              >
                <span className="album-selector-none">No album</span>
              </button>

              {/* Existing albums */}
              {albums.map((album) => (
                <button
                  key={album.id}
                  className={`album-selector-item ${selectedAlbumId === album.id ? 'selected' : ''}`}
                  onClick={() => handleSelectAlbum(album.id)}
                >
                  <div className="album-selector-thumb">
                    {album.cover_image ? (
                      <img
                        src={`http://localhost:8000/image/${album.cover_image.id}`}
                        alt=""
                      />
                    ) : (
                      <FolderPlus size={10} />
                    )}
                  </div>
                  <span className="album-selector-name">{album.name}</span>
                  <span className="album-selector-count">{album.image_count}</span>
                  {selectedAlbumId === album.id && (
                    <Check size={12} className="album-selector-check" />
                  )}
                </button>
              ))}

              {albums.length === 0 && !showCreateForm && (
                <div className="album-selector-empty">
                  No albums yet
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default AlbumSelector;
