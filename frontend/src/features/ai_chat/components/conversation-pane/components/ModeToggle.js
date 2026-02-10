/**
 * ModeToggle - RAG/Brain mode toggle buttons
 */
import React from 'react';
import { Search, Brain } from 'lucide-react';

function ModeToggle({ isBrainMode, onSetChatMode }) {
  return (
    <div className="mode-toggle">
      <button
        className={`mode-toggle-btn ${!isBrainMode ? 'active' : ''}`}
        onClick={() => onSetChatMode('rag')}
      >
        <Search size={14} />
        <span>RAG</span>
      </button>
      <button
        className={`mode-toggle-btn ${isBrainMode ? 'active' : ''}`}
        onClick={() => onSetChatMode('mnemosyne')}
      >
        <Brain size={14} />
        <span>Brain</span>
      </button>
    </div>
  );
}

export default ModeToggle;
