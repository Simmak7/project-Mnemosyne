import React, { useState, useCallback, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { FolderPlus, Check, Plus, X } from 'lucide-react';
import { useAlbums } from '../hooks/useAlbums';
import { API_URL } from '../../../utils/api';
import './AlbumPicker.css';

/**
 * AlbumPicker - Dropdown component for adding images to albums
 * Uses Portal to escape overflow:hidden containers (fixes vertical image issue)
 * Can create new albums inline
 */
function AlbumPicker({ imageIds, onClose, anchorRect }) {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newAlbumName, setNewAlbumName] = useState('');
  const [position, setPosition] = useState({ top: 0, left: 0, placement: 'bottom' });
  const pickerRef = useRef(null);

  const {
    albums,
    isLoading,
    createAlbum,
    addImagesToAlbum,
    isCreating
  } = useAlbums();

  // Calculate position based on anchor and viewport
  useEffect(() => {
    if (!anchorRect) return;

    const pickerHeight = 300; // max-height from CSS
    const pickerWidth = 240; // approximate width
    const padding = 8;

    const viewportHeight = window.innerHeight;
    const viewportWidth = window.innerWidth;

    // Check if there's enough space below
    const spaceBelow = viewportHeight - anchorRect.bottom;
    const spaceAbove = anchorRect.top;

    let top, left, placement;

    // Prefer below, but flip to above if not enough space
    if (spaceBelow >= pickerHeight + padding || spaceBelow >= spaceAbove) {
      top = anchorRect.bottom + 4;
      placement = 'bottom';
    } else {
      top = anchorRect.top - pickerHeight - 4;
      placement = 'top';
    }

    // Horizontal positioning - prefer right-aligned, but keep in viewport
    left = anchorRect.right - pickerWidth;
    if (left < padding) {
      left = padding;
    }
    if (left + pickerWidth > viewportWidth - padding) {
      left = viewportWidth - pickerWidth - padding;
    }

    setPosition({ top, left, placement });
  }, [anchorRect]);

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (pickerRef.current && !pickerRef.current.contains(e.target)) {
        onClose?.();
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  // Close on scroll
  useEffect(() => {
    const handleScroll = () => onClose?.();
    window.addEventListener('scroll', handleScroll, true);
    return () => window.removeEventListener('scroll', handleScroll, true);
  }, [onClose]);

  // Handle adding to existing album
  const handleAddToAlbum = useCallback((albumId) => {
    addImagesToAlbum({ albumId, imageIds });
    onClose?.();
  }, [addImagesToAlbum, imageIds, onClose]);

  // Handle creating new album and adding images
  const handleCreateAndAdd = useCallback((e) => {
    e.preventDefault();
    if (newAlbumName.trim()) {
      createAlbum(
        { name: newAlbumName.trim() },
        {
          onSuccess: (newAlbum) => {
            // Add images to the newly created album
            if (newAlbum?.id) {
              addImagesToAlbum({ albumId: newAlbum.id, imageIds });
            }
            onClose?.();
          }
        }
      );
    }
  }, [newAlbumName, createAlbum, addImagesToAlbum, imageIds, onClose]);

  const pickerContent = (
    <div
      ref={pickerRef}
      className={`album-picker-portal ${position.placement}`}
      style={{
        top: position.top,
        left: position.left
      }}
      onClick={(e) => e.stopPropagation()}
    >
      <div className="album-picker-header">
        <FolderPlus size={14} />
        <span>Add to Album</span>
      </div>

      {isLoading ? (
        <div className="album-picker-loading">Loading...</div>
      ) : (
        <div className="album-picker-list">
          {/* Create new album */}
          {showCreateForm ? (
            <form className="create-album-inline" onSubmit={handleCreateAndAdd}>
              <input
                type="text"
                value={newAlbumName}
                onChange={(e) => setNewAlbumName(e.target.value)}
                placeholder="New album name..."
                autoFocus
              />
              <button
                type="submit"
                className="inline-btn confirm"
                disabled={!newAlbumName.trim() || isCreating}
              >
                <Check size={12} />
              </button>
              <button
                type="button"
                className="inline-btn cancel"
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
              className="album-picker-item create-new"
              onClick={() => setShowCreateForm(true)}
            >
              <Plus size={14} />
              <span>Create new album</span>
            </button>
          )}

          {/* Existing albums */}
          {albums.map((album) => (
            <button
              key={album.id}
              className="album-picker-item"
              onClick={() => handleAddToAlbum(album.id)}
            >
              <div className="album-picker-thumb">
                {album.cover_image ? (
                  <img
                    src={`${API_URL}/image/${album.cover_image.id}`}
                    alt=""
                  />
                ) : (
                  <FolderPlus size={12} />
                )}
              </div>
              <span className="album-picker-name">{album.name}</span>
              <span className="album-picker-count">{album.image_count}</span>
            </button>
          ))}

          {albums.length === 0 && !showCreateForm && (
            <div className="album-picker-empty">
              No albums yet. Create one above!
            </div>
          )}
        </div>
      )}
    </div>
  );

  // Use Portal to render at document body level (escapes overflow:hidden)
  return createPortal(pickerContent, document.body);
}

export default AlbumPicker;
