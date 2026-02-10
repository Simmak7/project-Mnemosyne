import { useCallback, useMemo } from 'react';
import { arrayMove } from '@dnd-kit/sortable';
import { usePersistedState } from '../../../hooks/usePersistedState';
import { useNoteContext } from './NoteContext';

/**
 * useCustomNoteOrder - Per-category ordering stored in localStorage.
 * Returns ordered note IDs and a reorder handler.
 *
 * When sortBy !== 'custom', returns null (caller uses default sort).
 * When sortBy === 'custom', applies stored order and handles reorder.
 */
export function useCustomNoteOrder(notes) {
  const { currentCategory, sortBy } = useNoteContext();
  const storageKey = `note-order:${currentCategory}`;
  const [storedOrder, setStoredOrder] = usePersistedState(storageKey, null);

  // Build the ordered list of note IDs
  const orderedIds = useMemo(() => {
    if (sortBy !== 'custom' || !storedOrder) return null;

    const noteIds = new Set(notes.map(n => n.id));
    // Keep only IDs that still exist
    const validOrder = storedOrder.filter(id => noteIds.has(id));
    // Append any new notes at the top
    const newIds = notes
      .map(n => n.id)
      .filter(id => !validOrder.includes(id));
    return [...newIds, ...validOrder];
  }, [sortBy, storedOrder, notes]);

  // Apply custom order to notes array
  const orderedNotes = useMemo(() => {
    if (!orderedIds) return notes;
    const noteMap = new Map(notes.map(n => [n.id, n]));
    return orderedIds
      .map(id => noteMap.get(id))
      .filter(Boolean);
  }, [orderedIds, notes]);

  // Handle reorder via drag
  const handleReorder = useCallback((activeId, overId) => {
    const currentIds = orderedIds || notes.map(n => n.id);
    const oldIndex = currentIds.indexOf(activeId);
    const newIndex = currentIds.indexOf(overId);
    if (oldIndex === -1 || newIndex === -1) return;

    const newOrder = arrayMove(currentIds, oldIndex, newIndex);
    setStoredOrder(newOrder);
  }, [orderedIds, notes, setStoredOrder]);

  // Initialize custom order from current sort when first switching to custom
  const initializeOrder = useCallback(() => {
    if (!storedOrder) {
      setStoredOrder(notes.map(n => n.id));
    }
  }, [storedOrder, notes, setStoredOrder]);

  return {
    orderedNotes: sortBy === 'custom' ? orderedNotes : notes,
    orderedIds: orderedIds || notes.map(n => n.id),
    handleReorder,
    initializeOrder,
    isCustomSort: sortBy === 'custom',
  };
}

export default useCustomNoteOrder;
