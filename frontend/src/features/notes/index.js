/**
 * Notes Feature - Public Exports
 *
 * 3-pane note management interface inspired by Notion/Obsidian
 * with Neural Glass design integration
 */

// Main layout component
export { default as NoteLayout } from './components/NoteLayout';

// Individual components (for custom compositions)
export { default as NoteSidebar } from './components/NoteSidebar';
export { default as NoteList } from './components/NoteList';
export { default as NoteCard } from './components/NoteCard';
export { default as NoteSearchBar } from './components/NoteSearchBar';

// Detail panel components (Phase 3)
export { default as NoteDetail } from './components/NoteDetail';
export { default as NoteDetailHeader } from './components/NoteDetailHeader';
export { default as NoteDetailTabs } from './components/NoteDetailTabs';
export { default as NoteContentTab } from './components/NoteContentTab';
export { default as NoteContextTab } from './components/NoteContextTab';
export { default as NoteInfoTab } from './components/NoteInfoTab';
export { default as NoteMediaPreview } from './components/NoteMediaPreview';

// AI Tools (Phase 4)
export { default as AIToolsPanel } from './components/AIToolsPanel';

// Collection management
export { default as CollectionPicker } from './components/CollectionPicker';

// Context and hooks
export { NoteProvider, useNoteContext } from './hooks/NoteContext';
export { useNotes, useNoteSearch } from './hooks/useNotes';
export { useCollections, useCollectionNotes, useNoteCollections } from './hooks/useCollections';
