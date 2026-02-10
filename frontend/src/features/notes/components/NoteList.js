import React, { useCallback, useMemo, useEffect, useRef } from 'react';
import { FileText, Sparkles, Inbox, AlertCircle } from 'lucide-react';
import {
  SortableContext,
  verticalListSortingStrategy,
  rectSortingStrategy,
} from '@dnd-kit/sortable';
import { useNotes } from '../hooks/useNotes';
import { useNoteContext } from '../hooks/NoteContext';
import { useValidateNoteSelection } from '../hooks/useValidateNoteSelection';
import SortableNoteCard from './SortableNoteCard';
import DraggableNoteCard from './DraggableNoteCard';
import NoteSearchBar from './NoteSearchBar';
import './NoteList.css';

/**
 * NoteList - Center panel showing notes as cards.
 * Renders SortableContext when in custom sort mode, DraggableNoteCard otherwise.
 */
function NoteList({ onNoteSelect, onNoteOpen, orderedNotes, orderedIds, isCustomSort }) {
  const {
    currentCategory,
    selectedNoteId,
    selectNote,
    searchQuery,
    viewMode
  } = useNoteContext();

  const {
    notes: rawNotes,
    isLoading,
    isError,
    error,
    filteredCount
  } = useNotes();

  // Use DnD-ordered notes if provided, otherwise raw
  const notes = orderedNotes || rawNotes;

  // Clear persisted selection if note was deleted/trashed
  useValidateNoteSelection(notes, isLoading);

  // Category display info
  const categoryInfo = useMemo(() => ({
    inbox: { icon: Inbox, title: 'Inbox', description: 'Notes from the last 7 days' },
    smart: { icon: Sparkles, title: 'Smart Notes', description: 'AI-generated from images' },
    manual: { icon: FileText, title: 'Manual Notes', description: 'Notes you created' },
    daily: { icon: FileText, title: 'Daily Notes', description: 'Journal entries' },
    favorites: { icon: FileText, title: 'Favorites', description: 'Your starred notes' },
    review: { icon: AlertCircle, title: 'Review Queue', description: 'Notes needing attention' }
  }), []);

  const currentCategoryInfo = categoryInfo[currentCategory] || categoryInfo.inbox;
  const CategoryIcon = currentCategoryInfo.icon;

  const handleNoteClick = useCallback((note) => {
    selectNote(note.id);
    onNoteSelect?.(note);
  }, [selectNote, onNoteSelect]);

  const handleNoteDoubleClick = useCallback((note) => {
    onNoteOpen?.(note);
  }, [onNoteOpen]);

  const listRef = useRef(null);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      const tagName = e.target.tagName;
      const isEditable = e.target.isContentEditable;
      const isInEditor = e.target.closest?.('.ng-block-editor, .tiptap, .ProseMirror, [contenteditable="true"]');
      if (tagName === 'INPUT' || tagName === 'TEXTAREA' || isEditable || isInEditor) return;

      const noteIds = notes.map(n => n.id);
      const currentIndex = selectedNoteId ? noteIds.indexOf(selectedNoteId) : -1;

      switch (e.key) {
        case 'ArrowDown':
        case 'j':
          e.preventDefault();
          if (currentIndex < noteIds.length - 1) {
            selectNote(noteIds[currentIndex + 1]);
          } else if (currentIndex === -1 && noteIds.length > 0) {
            selectNote(noteIds[0]);
          }
          break;
        case 'ArrowUp':
        case 'k':
          e.preventDefault();
          if (currentIndex > 0) selectNote(noteIds[currentIndex - 1]);
          break;
        case 'Escape':
          selectNote(null);
          break;
        case 'Enter':
          if (selectedNoteId && onNoteOpen) {
            const selectedNote = notes.find(n => n.id === selectedNoteId);
            if (selectedNote) onNoteOpen(selectedNote);
          }
          break;
        default:
          break;
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [notes, selectedNoteId, selectNote, onNoteOpen]);

  const renderEmptyState = () => {
    if (isLoading) return null;
    const hasSearch = searchQuery?.trim();
    return (
      <div className="note-list-empty">
        <CategoryIcon size={48} className="empty-icon" />
        <h3>{hasSearch ? 'No matching notes' : `No ${currentCategoryInfo.title.toLowerCase()}`}</h3>
        <p>{hasSearch ? `No notes found for "${searchQuery}"` : currentCategoryInfo.description}</p>
      </div>
    );
  };

  const renderSkeleton = () => (
    <div className={`note-list-content ${viewMode}`}>
      {[1, 2, 3, 4, 5].map(i => (
        <div key={i} className="note-card-skeleton">
          <div className="skeleton-line title" />
          <div className="skeleton-line excerpt" />
          <div className="skeleton-line excerpt short" />
          <div className="skeleton-tags">
            <div className="skeleton-tag" />
            <div className="skeleton-tag" />
          </div>
        </div>
      ))}
    </div>
  );

  const CardComponent = isCustomSort ? SortableNoteCard : DraggableNoteCard;
  const strategy = viewMode === 'grid' ? rectSortingStrategy : verticalListSortingStrategy;

  const renderNotes = () => {
    const cards = notes.map((note, index) => (
      <CardComponent
        key={note.id}
        note={note}
        isSelected={selectedNoteId === note.id}
        onClick={() => handleNoteClick(note)}
        onDoubleClick={() => handleNoteDoubleClick(note)}
        searchQuery={searchQuery}
        style={{ animationDelay: `${index * 30}ms` }}
      />
    ));

    // Wrap in SortableContext when custom sort is active
    if (isCustomSort && orderedIds) {
      return (
        <SortableContext items={orderedIds} strategy={strategy}>
          <div className={`note-list-content ${viewMode}`} ref={listRef}>
            {cards}
          </div>
        </SortableContext>
      );
    }

    return (
      <div className={`note-list-content ${viewMode}`} ref={listRef}>
        {cards}
      </div>
    );
  };

  if (isError) {
    return (
      <div className="note-list">
        <NoteSearchBar resultCount={0} isLoading={false} />
        <div className="note-list-error">
          <AlertCircle size={48} />
          <h3>Failed to load notes</h3>
          <p>{error?.message || 'Something went wrong'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="note-list">
      <div className="note-list-header">
        <CategoryIcon size={20} className="category-icon" />
        <div className="category-info">
          <h2 className="category-title">{currentCategoryInfo.title}</h2>
          <p className="category-description">{currentCategoryInfo.description}</p>
        </div>
      </div>

      <NoteSearchBar resultCount={filteredCount} isLoading={isLoading} />

      {isLoading ? renderSkeleton() : notes.length === 0 ? renderEmptyState() : renderNotes()}
    </div>
  );
}

export default NoteList;
