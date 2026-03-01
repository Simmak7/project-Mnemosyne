import React, { useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Plus, ChevronLeft } from 'lucide-react';
import { useNoteContext } from '../../hooks/NoteContext';
import { useCollections } from '../../hooks/useCollections';
import { useCollectionActions } from './hooks';
import { NavigationCategories, CollectionsSection, SmartTagsSection } from './components';
import { useIsMobile } from '../../../../hooks/useIsMobile';
import { api } from '../../../../utils/api';
import '../NoteSidebar.css';

/**
 * NoteSidebar - Left navigation panel for notes
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
    selectNoteForEditing,
    refreshCounts,
    selectedCollectionId,
    setSelectedCollectionId
  } = useNoteContext();
  const queryClient = useQueryClient();
  const isMobile = useIsMobile();

  const [tagsExpanded, setTagsExpanded] = useState(!isMobile);
  const [collectionsExpanded, setCollectionsExpanded] = useState(!isMobile);

  const {
    collections,
    isLoading: collectionsLoading,
    createCollection,
    updateCollection,
    deleteCollection,
    isCreating
  } = useCollections();

  // Collection actions hook
  const collectionActions = useCollectionActions({
    collections,
    createCollection,
    updateCollection,
    deleteCollection,
    selectedCollectionId,
    setSelectedCollectionId,
    setCurrentCategory,
    isCreating,
  });

  const handleCategoryClick = useCallback((categoryId) => {
    setCurrentCategory(categoryId);
    setSelectedTagFilter(null);
    if (setSelectedCollectionId) setSelectedCollectionId(null);
  }, [setCurrentCategory, setSelectedTagFilter, setSelectedCollectionId]);

  const handleTagClick = useCallback((tagName) => {
    const newFilter = tagName === selectedTagFilter ? null : tagName;
    setSelectedTagFilter(newFilter);
    // Switch to All Notes when selecting a tag so count matches visible notes
    if (newFilter) {
      setCurrentCategory('all');
      if (setSelectedCollectionId) setSelectedCollectionId(null);
    }
  }, [selectedTagFilter, setSelectedTagFilter, setCurrentCategory, setSelectedCollectionId]);

  const handleCollectionClick = useCallback((collectionId) => {
    if (setSelectedCollectionId) {
      setSelectedCollectionId(collectionId === selectedCollectionId ? null : collectionId);
      setCurrentCategory('collection');
    }
  }, [selectedCollectionId, setSelectedCollectionId, setCurrentCategory]);

  const handleNewNote = useCallback(async () => {
    try {
      const newNote = await api.post('/notes/', {
        title: 'Untitled Note',
        content: ''
      });

      setCurrentCategory('all');
      await queryClient.invalidateQueries({ queryKey: ['notes-enhanced'] });
      refreshCounts();
      setTimeout(() => selectNoteForEditing(newNote.id), 100);
    } catch (error) {
      console.error('Error creating note:', error);
    }
  }, [setCurrentCategory, queryClient, refreshCounts, selectNote]);

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
      <NavigationCategories
        currentCategory={currentCategory}
        categoryCounts={categoryCounts}
        onCategoryClick={handleCategoryClick}
      />

      {/* Collections Section */}
      <CollectionsSection
        collectionsExpanded={collectionsExpanded}
        setCollectionsExpanded={setCollectionsExpanded}
        collections={collections}
        collectionsLoading={collectionsLoading}
        selectedCollectionId={selectedCollectionId}
        onCollectionClick={handleCollectionClick}
        collectionActions={collectionActions}
      />

      {/* Smart Tags Section */}
      <SmartTagsSection
        tagsExpanded={tagsExpanded}
        setTagsExpanded={setTagsExpanded}
        smartTags={smartTags}
        selectedTagFilter={selectedTagFilter}
        onTagClick={handleTagClick}
      />

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
