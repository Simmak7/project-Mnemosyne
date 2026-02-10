import React from 'react';
import {
  Plus,
  ChevronRight,
  ChevronDown,
  FolderOpen,
  MoreHorizontal,
  Pencil,
  Trash,
  X,
  Check
} from 'lucide-react';
import DroppableCollection from './DroppableCollection';

/**
 * Collections section with create/edit/delete functionality
 */
function CollectionsSection({
  collectionsExpanded,
  setCollectionsExpanded,
  collections,
  collectionsLoading,
  selectedCollectionId,
  onCollectionClick,
  collectionActions,
}) {
  const {
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
  } = collectionActions;

  return (
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

          {collectionsLoading && (
            <div className="collections-empty">
              <p>Loading...</p>
            </div>
          )}

          {!collectionsLoading && collections.length === 0 && !showCreateForm ? (
            <div className="collections-empty">
              <p>No collections yet</p>
            </div>
          ) : (
            collections.map((collection) => (
              <DroppableCollection key={collection.id} collectionId={collection.id}>
                <CollectionItem
                  collection={collection}
                  isSelected={selectedCollectionId === collection.id}
                  isEditing={editingCollectionId === collection.id}
                  editingName={editingName}
                  setEditingName={setEditingName}
                  contextMenuCollection={contextMenuCollection}
                  onCollectionClick={onCollectionClick}
                  onContextMenu={handleContextMenu}
                  onStartEdit={handleStartEdit}
                  onSubmitEdit={handleSubmitEdit}
                  onCancelEdit={handleCancelEdit}
                  onDelete={handleDeleteCollection}
                />
              </DroppableCollection>
            ))
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Individual collection item
 */
function CollectionItem({
  collection,
  isSelected,
  isEditing,
  editingName,
  setEditingName,
  contextMenuCollection,
  onCollectionClick,
  onContextMenu,
  onStartEdit,
  onSubmitEdit,
  onCancelEdit,
  onDelete,
}) {
  if (isEditing) {
    return (
      <div className="collection-item-wrapper">
        <form className="edit-collection-form" onSubmit={onSubmitEdit}>
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
              onClick={onCancelEdit}
            >
              <X size={14} />
            </button>
          </div>
        </form>
      </div>
    );
  }

  return (
    <div className="collection-item-wrapper">
      <div
        className={`collection-item ${isSelected ? 'active' : ''}`}
        onClick={() => onCollectionClick(collection.id)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onCollectionClick(collection.id);
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
          onClick={(e) => onContextMenu(e, collection)}
        >
          <MoreHorizontal size={14} />
        </button>
      </div>

      {contextMenuCollection?.id === collection.id && (
        <div className="collection-context-menu">
          <button
            className="context-menu-item"
            onClick={() => onStartEdit(collection)}
          >
            <Pencil size={14} />
            <span>Rename</span>
          </button>
          <button
            className="context-menu-item danger"
            onClick={() => onDelete(collection)}
          >
            <Trash size={14} />
            <span>Delete</span>
          </button>
        </div>
      )}
    </div>
  );
}

export default CollectionsSection;
