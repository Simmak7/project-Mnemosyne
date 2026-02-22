import React, { useState, useCallback } from 'react';
import {
  Images,
  Heart,
  FolderOpen,
  Trash2,
  Plus,
  ChevronRight,
  ChevronDown,
  MoreHorizontal,
  Pencil,
  Trash,
  X,
  Check
} from 'lucide-react';
import { useAlbums } from '../hooks/useAlbums';
import { API_URL } from '../../../utils/api';
import './GallerySidebar.css';

/**
 * GallerySidebar - Left navigation panel
 * Navigation: All Photos, Favorites, Albums, Trash
 */
function GallerySidebar({ currentView, selectedAlbumId, onViewChange }) {
  const [albumsExpanded, setAlbumsExpanded] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newAlbumName, setNewAlbumName] = useState('');
  const [editingAlbumId, setEditingAlbumId] = useState(null);
  const [editingName, setEditingName] = useState('');
  const [contextMenuAlbum, setContextMenuAlbum] = useState(null);

  const {
    albums,
    isLoading,
    createAlbum,
    updateAlbum,
    deleteAlbum,
    isCreating
  } = useAlbums();

  const navItems = [
    { id: 'all', label: 'All Photos', icon: Images, count: null },
    { id: 'favorites', label: 'Favorites', icon: Heart, count: null },
    { id: 'trash', label: 'Trash', icon: Trash2, count: null },
  ];

  const handleNavClick = useCallback((viewId) => {
    onViewChange(viewId, null);
  }, [onViewChange]);

  const handleAlbumClick = useCallback((albumId) => {
    onViewChange('album', albumId);
  }, [onViewChange]);

  const handleCreateAlbum = useCallback(() => {
    setShowCreateForm(true);
    setNewAlbumName('');
  }, []);

  const handleSubmitCreate = useCallback((e) => {
    e.preventDefault();
    if (newAlbumName.trim()) {
      createAlbum({ name: newAlbumName.trim() });
      setShowCreateForm(false);
      setNewAlbumName('');
    }
  }, [newAlbumName, createAlbum]);

  const handleCancelCreate = useCallback(() => {
    setShowCreateForm(false);
    setNewAlbumName('');
  }, []);

  const handleContextMenu = useCallback((e, album) => {
    e.preventDefault();
    e.stopPropagation();
    setContextMenuAlbum(contextMenuAlbum?.id === album.id ? null : album);
  }, [contextMenuAlbum]);

  const handleStartEdit = useCallback((album) => {
    setEditingAlbumId(album.id);
    setEditingName(album.name);
    setContextMenuAlbum(null);
  }, []);

  const handleSubmitEdit = useCallback((e) => {
    e.preventDefault();
    if (editingName.trim() && editingAlbumId) {
      updateAlbum({ albumId: editingAlbumId, name: editingName.trim() });
      setEditingAlbumId(null);
      setEditingName('');
    }
  }, [editingName, editingAlbumId, updateAlbum]);

  const handleCancelEdit = useCallback(() => {
    setEditingAlbumId(null);
    setEditingName('');
  }, []);

  const handleDeleteAlbum = useCallback((album) => {
    if (window.confirm(`Delete album "${album.name}"? Images won't be deleted.`)) {
      deleteAlbum(album.id);
      setContextMenuAlbum(null);
      // If viewing the deleted album, switch to all photos
      if (currentView === 'album' && selectedAlbumId === album.id) {
        onViewChange('all', null);
      }
    }
  }, [deleteAlbum, currentView, selectedAlbumId, onViewChange]);

  // Close context menu when clicking outside
  React.useEffect(() => {
    const handleClickOutside = () => setContextMenuAlbum(null);
    if (contextMenuAlbum) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [contextMenuAlbum]);

  return (
    <div className="gallery-sidebar">
      {/* Header */}
      <div className="sidebar-header">
        <h2 className="sidebar-title">Gallery</h2>
      </div>

      {/* Main Navigation */}
      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentView === item.id;

          return (
            <button
              key={item.id}
              className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
              onClick={() => handleNavClick(item.id)}
            >
              <Icon size={18} className="nav-icon" />
              <span className="nav-label">{item.label}</span>
              {item.count !== null && (
                <span className="nav-count">{item.count}</span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Albums Section */}
      <div className="sidebar-section">
        <button
          className="section-header"
          onClick={() => setAlbumsExpanded(!albumsExpanded)}
        >
          {albumsExpanded ? (
            <ChevronDown size={16} className="section-chevron" />
          ) : (
            <ChevronRight size={16} className="section-chevron" />
          )}
          <FolderOpen size={16} className="section-icon" />
          <span className="section-title">Albums</span>
          <span className="section-count">{albums.length}</span>
        </button>

        {albumsExpanded && (
          <div className="albums-list">
            {/* Create Album Button / Form */}
            {showCreateForm ? (
              <form className="create-album-form" onSubmit={handleSubmitCreate}>
                <input
                  type="text"
                  value={newAlbumName}
                  onChange={(e) => setNewAlbumName(e.target.value)}
                  placeholder="Album name..."
                  autoFocus
                  className="album-name-input"
                />
                <div className="create-album-actions">
                  <button
                    type="submit"
                    className="album-action-btn confirm"
                    disabled={!newAlbumName.trim() || isCreating}
                  >
                    <Check size={14} />
                  </button>
                  <button
                    type="button"
                    className="album-action-btn cancel"
                    onClick={handleCancelCreate}
                  >
                    <X size={14} />
                  </button>
                </div>
              </form>
            ) : (
              <button
                className="create-album-btn"
                onClick={handleCreateAlbum}
              >
                <Plus size={16} />
                <span>Create Album</span>
              </button>
            )}

            {/* Loading State */}
            {isLoading && (
              <div className="albums-loading">
                <span>Loading albums...</span>
              </div>
            )}

            {/* Album Items */}
            {!isLoading && albums.length === 0 && !showCreateForm ? (
              <div className="albums-empty">
                <p>No albums yet</p>
              </div>
            ) : (
              albums.map((album) => (
                <div key={album.id} className="album-item-wrapper">
                  {editingAlbumId === album.id ? (
                    <form className="edit-album-form" onSubmit={handleSubmitEdit}>
                      <input
                        type="text"
                        value={editingName}
                        onChange={(e) => setEditingName(e.target.value)}
                        autoFocus
                        className="album-name-input"
                      />
                      <div className="create-album-actions">
                        <button
                          type="submit"
                          className="album-action-btn confirm"
                          disabled={!editingName.trim()}
                        >
                          <Check size={14} />
                        </button>
                        <button
                          type="button"
                          className="album-action-btn cancel"
                          onClick={handleCancelEdit}
                        >
                          <X size={14} />
                        </button>
                      </div>
                    </form>
                  ) : (
                    <button
                      className={`album-item ${
                        currentView === 'album' && selectedAlbumId === album.id
                          ? 'active'
                          : ''
                      }`}
                      onClick={() => handleAlbumClick(album.id)}
                    >
                      <div className="album-thumbnail">
                        {album.cover_image ? (
                          <img
                            src={`${API_URL}/image/${album.cover_image.id}`}
                            alt=""
                          />
                        ) : (
                          <FolderOpen size={16} />
                        )}
                      </div>
                      <span className="album-name">{album.name}</span>
                      <span className="album-count">{album.image_count}</span>
                      <button
                        className="album-menu-btn"
                        onClick={(e) => handleContextMenu(e, album)}
                      >
                        <MoreHorizontal size={14} />
                      </button>
                    </button>
                  )}

                  {/* Context Menu */}
                  {contextMenuAlbum?.id === album.id && (
                    <div className="album-context-menu">
                      <button
                        className="context-menu-item"
                        onClick={() => handleStartEdit(album)}
                      >
                        <Pencil size={14} />
                        <span>Rename</span>
                      </button>
                      <button
                        className="context-menu-item danger"
                        onClick={() => handleDeleteAlbum(album)}
                      >
                        <Trash size={14} />
                        <span>Delete</span>
                      </button>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default GallerySidebar;
