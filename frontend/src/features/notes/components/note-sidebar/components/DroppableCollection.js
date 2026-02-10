import React from 'react';
import { useDroppable } from '@dnd-kit/core';

/**
 * DroppableCollection - useDroppable wrapper for collection items.
 * Drop zone ID is prefixed with 'collection-' so the DnD handler can
 * distinguish collection drops from note-reorder drops.
 */
function DroppableCollection({ collectionId, children }) {
  const { setNodeRef, isOver } = useDroppable({
    id: `collection-${collectionId}`,
  });

  return (
    <div
      ref={setNodeRef}
      className={`collection-droppable ${isOver ? 'is-drag-over' : ''}`}
    >
      {children}
    </div>
  );
}

export default DroppableCollection;
