import React from 'react';
import { useDraggable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import NoteCard from './NoteCard';

/**
 * DraggableNoteCard - useDraggable wrapper around NoteCard.
 * Used when sortBy !== 'custom' (can drag to collection, auto-switches to custom on reorder).
 */
function DraggableNoteCard({ note, isSelected, onClick, onDoubleClick, searchQuery, style: externalStyle }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    isDragging,
  } = useDraggable({ id: note.id });

  const style = {
    ...externalStyle,
    transform: transform ? CSS.Translate.toString(transform) : undefined,
    opacity: isDragging ? 0.4 : 1,
    zIndex: isDragging ? 10 : undefined,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`draggable-note-wrapper ${isDragging ? 'is-dragging' : ''}`}
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

export default DraggableNoteCard;
