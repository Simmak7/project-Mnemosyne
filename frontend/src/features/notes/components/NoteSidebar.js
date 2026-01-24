import React, { useState, useCallback, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  Inbox,
  Sparkles,
  FileText,
  Calendar,
  Heart,
  Clock,
  Trash2,
  Hash,
  Plus,
  ChevronRight,
  ChevronDown,
  ChevronLeft,
  FolderOpen,
  MoreHorizontal,
  Pencil,
  Trash,
  X,
  Check
} from 'lucide-react';
import { useNoteContext } from '../hooks/NoteContext';
import { useCollections } from '../hooks/useCollections';
import './NoteSidebar.css';

/**
 * NoteSidebar - Left navigation panel for notes
 * Categories: Inbox, Smart Notes, Manual Notes, Daily Notes, Favorites, Review Queue
 * Smart Tags: Auto-extracted popular tags
 */
function NoteSidebar({ isCollapsed, onCollapse }) {
  const {
    currentCategory,
    setCurrentCategory,
    categoryCounts,
    smartTags,
    selectedTagFilter,
    setSelectedTagFilter,
    selectNote,
    refreshCounts,
    selectedCollectionId,
    setSelectedCollectionId
  } = useNoteContext();
  const queryClient = useQueryClient();

  const [tagsExpanded, setTagsExpanded] = useState(true);
  const [collectionsExpanded, setCollectionsExpanded] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newCollectionName, setNewCollectionName] = useState('');
  const [editingCollectionId, setEditingCollectionId] = useState(null);
  const [editingName, setEditingName] = useState('');
  const [contextMenuCollection, setContextMenuCollection] = useState(null);

  const {
    collections,
    isLoading: collectionsLoading,
    createCollection,
    updateCollection,
    deleteCollection,
    isCreating
  } = useCollections();

  // Navigation categories
  const categories = [
    { id: 'inbox', label: 'Inbox', icon: Inbox, description: 'New & recent notes' },
    { id: 'smart', label: 'Smart Notes', icon: Sparkles, description: 'AI-generated notes' },
    { id: 'manual', label: 'Manual Notes', icon: FileText, description: 'User-created notes' },
    { id: 'daily', label: 'Daily Notes', icon: Calendar, description: 'Journal entries' },
    { id: 'favorites', label: 'Favorites', icon: Heart, description: 'Starred notes' },
    { id: 'review', label: 'Review Queue', icon: Clock, description: 'Needs attention', badge: true },
    { id: 'trash', label: 'Trash', icon: Trash2, description: 'Deleted notes (15 days)', isDanger: true }
  ];

  const handleCategoryClick = useCallback((categoryId) => {
    setCurrentCategory(categoryId);
    setSelectedTagFilter(null);
    if (setSelectedCollectionId) setSelectedCollectionId(null);
  }, [setCurrentCategory, setSelectedTagFilter, setSelectedCollectionId]);

  const handleTagClick = useCallback((tagName) => {
    setSelectedTagFilter(tagName === selectedTagFilter ? null : tagName);
  }, [selectedTagFilter, setSelectedTagFilter]);

  const handleNewNote = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await fetch('http://localhost:8000/notes/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          title: 'Untitled Note',
          content: ''
        })
      });

      if (response.ok) {
        const newNote = await response.json();
        // Navigate to inbox and select the new note
        setCurrentCategory('inbox');
        // Refresh notes list
        await queryClient.invalidateQueries({ queryKey: ['notes-enhanced'] });
        refreshCounts();
        // Select the new note after a short delay to let the list refresh
        setTimeout(() => selectNote(newNote.id), 100);
      }
    } catch (error) {
      console.error('Error creating note:', error);
    }
  }, [setCurrentCategory, queryClient, refreshCounts, selectNote]);

  // Collection handlers
  const handleCollectionClick = useCallback((collectionId) => {
    if (setSelectedCollectionId) {
      setSelectedCollectionId(collectionId === selectedCollectionId ? null : collectionId);
      setCurrentCategory('collection');
    }
  }, [selectedCollectionId, setSelectedCollectionId, setCurrentCategory]);

  const handleCreateCollection = useCallback(() => {
    setShowCreateForm(true);
    setNewCollectionName('');
  }, []);

  const handleSubmitCreate = useCallback((e) => {
    e.preventDefault();
    if (newCollectionName.trim()) {
      createCollection({ name: newCollectionName.trim() });
      setShowCreateForm(false);
      setNewCollectionName('');
    }
  }, [newCollectionName, createCollection]);

  const handleCancelCreate = useCallback(() => {
    setShowCreateForm(false);
    setNewCollectionName('');
  }, []);

  const handleContextMenu = useCallback((e, collection) => {
    e.preventDefault();
    e.stopPropagation();
    setContextMenuCollection(contextMenuCollection?.id === collection.id ? null : collection);
  }, [contextMenuCollection]);

  const handleStartEdit = useCallback((collection) => {
    setEditingCollectionId(collection.id);
    setEditingName(collection.name);
    setContextMenuCollection(null);
  }, []);

  const handleSubmitEdit = useCallback((e) => {
    e.preventDefault();
    if (editingName.trim() && editingCollectionId) {
      updateCollection({ collectionId: editingCollectionId, name: editingName.trim() });
      setEditingCollectionId(null);
      setEditingName('');
    }
  }, [editingName, editingCollectionId, updateCollection]);

  const handleCancelEdit = useCallback(() => {
    setEditingCollectionId(null);
    setEditingName('');
  }, []);

  const handleDeleteCollection = useCallback((collection) => {
    if (window.confirm(`Delete collection "${collection.name}"? Notes won't be deleted.`)) {
      deleteCollection(collection.id);
      setContextMenuCollection(null);
      if (selectedCollectionId === collection.id && setSelectedCollectionId) {
        setSelectedCollectionId(null);
        setCurrentCategory('inbox');
      }
    }
  }, [deleteCollection, selectedCollectionId, setSelectedCollectionId, setCurrentCategory]);

  // Close context menu when clicking outside
  useEffect(() => {
    const handleClickOutside = () => setContextMenuCollection(null);
    if (contextMenuCollection) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [contextMenuCollection]);

  // Don't render anything if collapsed - the floating button is in NoteLayout
  if (isCollapsed) {
    return null;
  }

  return (
    <div className="note-sidebar">
      {/* Header */}
      <div className="sidebar-header">
        <h2 className="sidebar-title">Notes</h2>
        {onCollapse && (
          <button
            className="sidebar-collapse-btn"
            onClick={onCollapse}
            title="Collapse sidebar"
          >
            <ChevronLeft size={18} />
          </button>
        )}
      </div>

      {/* Main Navigation */}
      <nav className="sidebar-nav">
        {categories.map((category) => {
          const Icon = category.icon;
          const isActive = currentCategory === category.id;
          const count = categoryCounts[category.id] || 0;

          return (
            <button
              key={category.id}
              className={`sidebar-nav-item ${isActive ? 'active' : ''} ${category.isDanger ? 'danger-item' : ''}`}
              onClick={() => handleCategoryClick(category.id)}
              title={category.description}
            >
              <Icon size={18} className="nav-icon" />
              <span className="nav-label">{category.label}</span>
              {category.badge && count > 0 ? (
                <span className="nav-badge">{count}</span>
              ) : count > 0 ? (
                <span className="nav-count">{count}</span>
              ) : null}
            </button>
          );
        })}
      </nav>

      {/* Note Collections Section */}
      <div className="sidebar-section" style={{ flex: 'none' }}>
        <button
          className="section-header"
          onClick={() => setCollectionsExpanded(!collectionsExpanded)}
        >
          {collectionsExpanded ? (
            <ChevronDown size={16} className="section-chevron" />
          ) : (
            <ChevronRight size={16} className="section-chevron" />
          )}
          <FolderOpen size={16} className="section-icon" />
          <span className="section-title">Collections</span>
          <span className="section-count">{collections.length}</span>
        </button>

        {collectionsExpanded && (
          <div className="collections-list">
            {/* Create Collection Button / Form */}
            {showCreateForm ? (
              <form className="create-collection-form" onSubmit={handleSubmitCreate}>
                <input
                  type="text"
                  value={newCollectionName}
                  onChange={(e) => setNewCollectionName(e.target.value)}
                  placeholder="Collection name..."
                  autoFocus
                  className="collection-name-input"
                />
                <div className="create-collection-actions">
                  <button
                    type="submit"
                    className="collection-action-btn confirm"
                    disabled={!newCollectionName.trim() || isCreating}
                  >
                    <Check size={14} />
                  </button>
                  <button
                    type="button"
                    className="collection-action-btn cancel"
                    onClick={handleCancelCreate}
                  >
                    <X size={14} />
                  </button>
                </div>
              </form>
            ) : (
              <button
                className="create-collection-btn"
                onClick={handleCreateCollection}
              >
                <Plus size={16} />
                <span>New Collection</span>
              </button>
            )}

            {/* Loading State */}
            {collectionsLoading && (
              <div className="collections-empty">
                <p>Loading...</p>
              </div>
            )}

            {/* Collection Items */}
            {!collectionsLoading && collections.length === 0 && !showCreateForm ? (
              <div className="collections-empty">
                <p>No collections yet</p>
              </div>
            ) : (
              collections.map((collection) => (
                <div key={collection.id} className="collection-item-wrapper">
                  {editingCollectionId === collection.id ? (
                    <form className="edit-collection-form" onSubmit={handleSubmitEdit}>
                      <input
                        type="text"
                        value={editingName}
                        onChange={(e) => setEditingName(e.target.value)}
                        autoFocus
                        className="collection-name-input"
                      />
                      <div className="create-collection-actions">
                        <button
                          type="submit"
                          className="collection-action-btn confirm"
                          disabled={!editingName.trim()}
                        >
                          <Check size={14} />
                        </button>
                        <button
                          type="button"
                          className="collection-action-btn cancel"
                          onClick={handleCancelEdit}
                        >
                          <X size={14} />
                        </button>
                      </div>
                    </form>
                  ) : (
                    <div
                      className={`collection-item ${
                        selectedCollectionId === collection.id ? 'active' : ''
                      }`}
                      onClick={() => handleCollectionClick(collection.id)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          handleCollectionClick(collection.id);
                        }
                      }}
                    >
                      {collection.icon ? (
                        <span className="collection-icon">{collection.icon}</span>
                      ) : (
                        <FolderOpen size={16} className="collection-icon-placeholder" />
                      )}
                      <span className="collection-name">{collection.name}</span>
                      <span className="collection-count">{collection.note_count}</span>
                      <button
                        className="collection-menu-btn"
                        onClick={(e) => handleContextMenu(e, collection)}
                      >
                        <MoreHorizontal size={14} />
                      </button>
                    </div>
                  )}

                  {/* Context Menu */}
                  {contextMenuCollection?.id === collection.id && (
                    <div className="collection-context-menu">
                      <button
                        className="context-menu-item"
                        onClick={() => handleStartEdit(collection)}
                      >
                        <Pencil size={14} />
                        <span>Rename</span>
                      </button>
                      <button
                        className="context-menu-item danger"
                        onClick={() => handleDeleteCollection(collection)}
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

      {/* Smart Tags Section */}
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
                  onClick={() => handleTagClick(tag.name)}
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

      {/* New Note Button */}
      <div className="sidebar-footer">
        <button className="new-note-btn" onClick={handleNewNote}>
          <Plus size={18} />
          <span>New Note</span>
        </button>
      </div>
    </div>
  );
}

export default NoteSidebar;
