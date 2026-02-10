import React from 'react';
import { JournalProvider } from '../hooks/JournalContext';
import JournalLayoutInner from './JournalLayoutInner';

/**
 * JournalLayout - Wraps JournalProvider around the 3-pane layout.
 */
function JournalLayout({ onNavigateToNote, onNavigateToImage }) {
  return (
    <JournalProvider>
      <JournalLayoutInner
        onNavigateToNote={onNavigateToNote}
        onNavigateToImage={onNavigateToImage}
      />
    </JournalProvider>
  );
}

export default JournalLayout;
