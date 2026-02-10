import { useState, useCallback } from 'react';
import {
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import { sortableKeyboardCoordinates } from '@dnd-kit/sortable';
import { useNoteContext } from './NoteContext';

/**
 * useNoteDragDrop - DnD sensors, drag state, and event handlers.
 *
 * @param {Function} onReorder - called with (activeId, overId) for sort reorder
 * @param {Function} onDropToCollection - called with (noteId, collectionId)
 * @param {Function} initializeOrder - called to init custom order on first drag-reorder
 */
export function useNoteDragDrop({ onReorder, onDropToCollection, initializeOrder }) {
  const { sortBy, setSortBy, setSortOrder } = useNoteContext();
  const [activeId, setActiveId] = useState(null);

  // 8px activation distance prevents drag on normal click
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const handleDragStart = useCallback((event) => {
    setActiveId(event.active.id);
  }, []);

  const handleDragEnd = useCallback((event) => {
    const { active, over } = event;
    setActiveId(null);

    if (!over || active.id === over.id) return;

    // Check if dropped on a collection (droppable IDs prefixed with 'collection-')
    const overId = String(over.id);
    if (overId.startsWith('collection-')) {
      const collectionId = parseInt(overId.replace('collection-', ''), 10);
      if (collectionId && onDropToCollection) {
        onDropToCollection(active.id, collectionId);
      }
      return;
    }

    // Dropped on another note → reorder
    if (sortBy !== 'custom') {
      // Auto-switch to custom sort mode
      setSortBy('custom');
      setSortOrder('desc');
      initializeOrder?.();
    }
    onReorder?.(active.id, over.id);
  }, [sortBy, setSortBy, setSortOrder, onReorder, onDropToCollection, initializeOrder]);

  const handleDragCancel = useCallback(() => {
    setActiveId(null);
  }, []);

  return {
    sensors,
    activeId,
    handleDragStart,
    handleDragEnd,
    handleDragCancel,
  };
}

export default useNoteDragDrop;
