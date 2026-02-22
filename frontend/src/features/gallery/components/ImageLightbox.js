import React, { useEffect, useCallback, useState, useRef } from 'react';
import { createPortal } from 'react-dom';
import {
  X,
  ChevronLeft,
  ChevronRight,
  Heart,
  Trash2,
  ExternalLink,
  Calendar,
  Tag,
  FileText,
  RefreshCw,
  FolderPlus,
  Pencil,
  Check,
  MessageSquare
} from 'lucide-react';
import AlbumPicker from './AlbumPicker';
import { API_URL } from '../../../utils/api';
import './ImageLightbox.css';

/**
 * ImageLightbox - Full-screen image viewer with metadata
 * Features: Navigation, metadata display, actions
 */
function ImageLightbox({
  image,
  onClose,
  onNavigate,
  onNavigateToNote,
  onNavigateToAI,
  onFavorite,
  onDelete,
  onRetry,
  onAddToAlbum,
  onRename
}) {
  // Local state for instant favorite toggle feedback
  const [localFavorite, setLocalFavorite] = useState(image.is_favorite);
  const [showAlbumPicker, setShowAlbumPicker] = useState(false);
  const [albumBtnRect, setAlbumBtnRect] = useState(null);
  const albumBtnRef = useRef(null);

  // Rename state
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(image.display_name || '');
  const editInputRef = useRef(null);

  const isFailed = image.ai_analysis_status === 'failed';
  const isProcessing = image.ai_analysis_status === 'processing';

  // Sync local favorite state with prop changes (e.g., when navigating between images)
  useEffect(() => {
    setLocalFavorite(image.is_favorite);
  }, [image.id, image.is_favorite]);

  // Reset rename state when image changes
  useEffect(() => {
    setIsEditing(false);
    setEditName(image.display_name || '');
  }, [image.id, image.display_name]);

  // Focus input when editing starts
  useEffect(() => {
    if (isEditing && editInputRef.current) {
      editInputRef.current.focus();
      editInputRef.current.select();
    }
  }, [isEditing]);

  // Handle favorite click with instant local feedback
  const handleFavoriteClick = useCallback(() => {
    setLocalFavorite(prev => !prev);
    onFavorite?.();
  }, [onFavorite]);

  // Handle album button click
  const handleAlbumClick = useCallback(() => {
    if (albumBtnRef.current) {
      setAlbumBtnRect(albumBtnRef.current.getBoundingClientRect());
    }
    setShowAlbumPicker(true);
  }, []);

  // Handle retry click
  const handleRetryClick = useCallback(() => {
    onRetry?.();
  }, [onRetry]);

  // Handle rename
  const handleStartEditing = useCallback(() => {
    setEditName(image.display_name || image.filename || '');
    setIsEditing(true);
  }, [image.display_name, image.filename]);

  const handleCancelEditing = useCallback(() => {
    setIsEditing(false);
    setEditName(image.display_name || '');
  }, [image.display_name]);

  const handleSaveRename = useCallback(() => {
    const trimmedName = editName.trim();
    if (trimmedName && trimmedName !== image.display_name) {
      onRename?.(image.id, trimmedName);
    }
    setIsEditing(false);
  }, [editName, image.id, image.display_name, onRename]);

  const handleRenameKeyDown = useCallback((e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSaveRename();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleCancelEditing();
    }
  }, [handleSaveRename, handleCancelEditing]);

  // Handle "Ask AI about this image"
  const handleAskAI = useCallback(() => {
    if (onNavigateToAI) {
      onNavigateToAI({
        type: 'image',
        id: image.id,
        title: image.display_name || image.filename
      });
      onClose();
    }
  }, [onNavigateToAI, onClose, image]);

  // Keyboard navigation (disabled when editing)
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Don't handle shortcuts when editing
      if (isEditing) return;

      // Don't handle single-key shortcuts when any input is focused (e.g. album name)
      const activeEl = document.activeElement;
      const isInputFocused = activeEl && (
        activeEl.tagName === 'INPUT' ||
        activeEl.tagName === 'TEXTAREA' ||
        activeEl.isContentEditable
      );
      if (isInputFocused) return;

      switch (e.key) {
        case 'Escape':
          onClose();
          break;
        case 'ArrowLeft':
          onNavigate('prev');
          break;
        case 'ArrowRight':
          onNavigate('next');
          break;
        case 'f':
          handleFavoriteClick();
          break;
        case 'r':
          handleStartEditing();
          break;
        case 'a':
          if (onNavigateToAI) {
            handleAskAI();
          }
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'auto';
    };
  }, [onClose, onNavigate, handleFavoriteClick, handleStartEditing, handleAskAI, onNavigateToAI, isEditing]);

  const handleBackdropClick = useCallback((e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  }, [onClose]);

  const handleViewNote = useCallback((noteId) => {
    if (onNavigateToNote) {
      onNavigateToNote(noteId);
      onClose();
    }
  }, [onNavigateToNote, onClose]);

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString(undefined, {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return createPortal(
    <div className="lightbox-overlay" onClick={handleBackdropClick}>
      {/* Navigation buttons */}
      <button
        className="lightbox-nav prev"
        onClick={() => onNavigate('prev')}
        aria-label="Previous image"
      >
        <ChevronLeft size={32} />
      </button>

      <button
        className="lightbox-nav next"
        onClick={() => onNavigate('next')}
        aria-label="Next image"
      >
        <ChevronRight size={32} />
      </button>

      {/* Main content */}
      <div className="lightbox-content" onClick={(e) => e.stopPropagation()}>
        {/* Top bar: title + actions */}
        <div className="lightbox-top-bar">
          <div className="lightbox-title-area">
            {isEditing ? (
              <div className="lightbox-title-edit">
                <input
                  ref={editInputRef}
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  onKeyDown={handleRenameKeyDown}
                  onBlur={handleSaveRename}
                  className="title-input"
                  placeholder="Enter name..."
                />
                <button
                  className="action-btn save"
                  onClick={handleSaveRename}
                  title="Save (Enter)"
                >
                  <Check size={16} />
                </button>
              </div>
            ) : (
              <div className="lightbox-title-display">
                <h2 className="lightbox-title" title={image.display_name || image.filename}>
                  {image.display_name || image.filename}
                </h2>
                <button
                  className="action-btn edit"
                  onClick={handleStartEditing}
                  title="Rename (R)"
                >
                  <Pencil size={13} />
                </button>
              </div>
            )}
          </div>

          <div className="lightbox-actions">
            {isProcessing && (
              <span className="action-btn analyzing" title="AI analysis in progress">
                <RefreshCw size={16} className="spin" />
              </span>
            )}
            {isFailed && (
              <button
                className="action-btn retry"
                onClick={handleRetryClick}
                title="Retry AI analysis"
              >
                <RefreshCw size={16} />
              </button>
            )}
            <button
              className={`action-btn fav ${localFavorite ? 'active' : ''}`}
              onClick={handleFavoriteClick}
              title={localFavorite ? 'Remove from favorites (F)' : 'Add to favorites (F)'}
            >
              <Heart size={16} fill={localFavorite ? 'currentColor' : 'none'} />
            </button>
            <button
              ref={albumBtnRef}
              className="action-btn album"
              onClick={handleAlbumClick}
              title="Add to album"
            >
              <FolderPlus size={16} />
            </button>
            {showAlbumPicker && (
              <AlbumPicker
                imageIds={[image.id]}
                onClose={() => setShowAlbumPicker(false)}
                anchorRect={albumBtnRect}
              />
            )}
            {onNavigateToAI && (
              <button
                className="action-btn ai"
                onClick={handleAskAI}
                title="Ask AI about this image (A)"
              >
                <MessageSquare size={16} />
              </button>
            )}
            <button
              className="action-btn delete"
              onClick={onDelete}
              title="Delete"
            >
              <Trash2 size={16} />
            </button>
            <div className="lightbox-actions-divider" />
            <button
              className="action-btn close"
              onClick={onClose}
              title="Close (Esc)"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Main area: image + sidebar */}
        <div className="lightbox-main">
          <div className="lightbox-image-container">
            <img
              src={`${API_URL}/image/${image.id}`}
              alt={image.filename}
              className="lightbox-image"
            />
          </div>

          {/* Info sidebar */}
          <div className="lightbox-sidebar">
            <div className="lightbox-meta">
              <div className="meta-row">
                <Calendar size={13} className="meta-icon" />
                <span className="meta-label">Uploaded</span>
                <span className="meta-value">{formatDate(image.uploaded_at)}</span>
              </div>

              {image.tags && image.tags.length > 0 && (
                <div className="meta-section">
                  <div className="meta-section-header">
                    <Tag size={13} />
                    <span>Tags</span>
                  </div>
                  <div className="lightbox-tags">
                    {image.tags.map(tag => (
                      <span key={tag.id} className="lightbox-tag">
                        #{tag.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {image.notes && image.notes.filter(Boolean).length > 0 && (
                <div className="meta-section">
                  <div className="meta-section-header">
                    <FileText size={13} />
                    <span>Notes ({image.notes.filter(Boolean).length})</span>
                  </div>
                  <div className="lightbox-notes">
                    {image.notes.filter(Boolean).map(note => (
                      <div
                        key={note.id}
                        className="note-card"
                        onClick={() => handleViewNote(note.id)}
                        onKeyDown={(e) => e.key === 'Enter' && handleViewNote(note.id)}
                        role="button"
                        tabIndex={0}
                      >
                        <div className="note-title">{note.title || 'Untitled Note'}</div>
                        <div className="note-preview">
                          {(note.content || '').substring(0, 120)}
                          {(note.content || '').length > 120 && '...'}
                        </div>
                        <div className="note-card-hint">
                          Open note <ExternalLink size={10} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Keyboard shortcuts - full width bottom */}
        <div className="lightbox-shortcuts">
          <span>← → Navigate</span>
          <span>F Favorite</span>
          <span>R Rename</span>
          {onNavigateToAI && <span>A Ask AI</span>}
          <span>Esc Close</span>
        </div>
      </div>
    </div>,
    document.body
  );
}

export default ImageLightbox;
