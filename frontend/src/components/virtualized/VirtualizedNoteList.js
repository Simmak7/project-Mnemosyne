/**
 * Re-export VirtualizedNoteList from refactored location
 * This file maintains backward compatibility with existing imports
 */
export { default } from './virtualized-note-list';
export {
  VirtualizedNoteList,
  NoteCard,
  NoteDetailPanel,
  NoteEditorModal,
  useNoteList,
  formatDate,
  getSnippet,
  highlightText,
} from './virtualized-note-list';
