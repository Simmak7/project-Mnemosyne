import React from 'react';
import { NoteProvider } from '../hooks/NoteContext';
import NoteLayoutInner from './NoteLayoutInner';

/**
 * NoteLayout - Wraps NoteProvider around the panel layout.
 * All panel + DnD logic lives in NoteLayoutInner.
 */
function NoteLayout({ onNavigateToGraph, onNavigateToImage, onNavigateToAI, onNavigateToDocument, selectedNoteId, initialSearchQuery }) {
  return (
    <NoteProvider initialNoteId={selectedNoteId} initialSearchQuery={initialSearchQuery}>
      <NoteLayoutInner
        onNavigateToGraph={onNavigateToGraph}
        onNavigateToImage={onNavigateToImage}
        onNavigateToAI={onNavigateToAI}
        onNavigateToDocument={onNavigateToDocument}
      />
    </NoteProvider>
  );
}

export default NoteLayout;
