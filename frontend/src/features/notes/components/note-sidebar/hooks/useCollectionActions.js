import { useState, useEffect, useCallback } from 'react';

/**
 * Hook for managing collection CRUD actions
 */
export function useCollectionActions({
  collections,
  createCollection,
  updateCollection,
  deleteCollection,
  selectedCollectionId,
  setSelectedCollectionId,
  setCurrentCategory,
  isCreating,
}) {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newCollectionName, setNewCollectionName] = useState('');
  const [editingCollectionId, setEditingCollectionId] = useState(null);
  const [editingName, setEditingName] = useState('');
  const [contextMenuCollection, setContextMenuCollection] = useState(null);

  // Close context menu when clicking outside
  useEffect(() => {
    const handleClickOutside = () => setContextMenuCollection(null);
    if (contextMenuCollection) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [contextMenuCollection]);

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

  return {
    showCreateForm,
    newCollectionName,
    setNewCollectionName,
    editingCollectionId,
    editingName,
    setEditingName,
    contextMenuCollection,
    handleCreateCollection,
    handleSubmitCreate,
    handleCancelCreate,
    handleContextMenu,
    handleStartEdit,
    handleSubmitEdit,
    handleCancelEdit,
    handleDeleteCollection,
    isCreating,
  };
}
