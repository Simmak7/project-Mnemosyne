import React from 'react';
import { NoteProvider } from '../hooks/NoteContext';
import NoteLayoutInner from './NoteLayoutInner';

/**
 * NoteLayout - Wraps NoteProvider around the panel layout.
 * All panel + DnD logic lives in NoteLayoutInner.
 */
function NoteLayout({ onNavigateToGraph, onNavigateToImage, onNavigateToAI, onNavigateToDocument, selectedNoteId }) {
  return (
    <NoteProvider initialNoteId={selectedNoteId}>
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
