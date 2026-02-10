import React from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import NoteCard from './NoteCard';

/**
 * SortableNoteCard - useSortable wrapper around NoteCard.
 * Used when sortBy === 'custom' (drag to reorder).
 */
function SortableNoteCard({ note, isSelected, onClick, onDoubleClick, searchQuery, style: externalStyle }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: note.id });

  const style = {
    ...externalStyle,
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
    zIndex: isDragging ? 10 : undefined,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`sortable-note-wrapper ${isDragging ? 'is-dragging' : ''}`}
      {...attributes}
      {...listeners}
    >
      <NoteCard
        note={note}
        isSelected={isSelected}
        onClick={onClick}
        onDoubleClick={onDoubleClick}
        searchQuery={searchQuery}
      />
    </div>
  );
}

export default SortableNoteCard;
