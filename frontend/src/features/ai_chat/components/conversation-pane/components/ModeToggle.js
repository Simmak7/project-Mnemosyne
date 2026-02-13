/**
 * ModeToggle - NEXUS RAG / ZAIA AI / Legacy RAG mode toggle
 */
import React from 'react';
import { Search, Brain, Network } from 'lucide-react';

const legacyRagEnabled = localStorage.getItem('ENABLE_LEGACY_RAG') === 'true';

function ModeToggle({ chatMode, onSetChatMode }) {
  return (
    <div className="mode-toggle">
      {legacyRagEnabled && (
        <button
          className={`mode-toggle-btn ${chatMode === 'rag' ? 'active' : ''}`}
          onClick={() => onSetChatMode('rag')}
        >
          <Search size={14} />
          <span>RAG</span>
        </button>
      )}
      <button
        className={`mode-toggle-btn nexus ${chatMode === 'nexus' ? 'active' : ''}`}
        onClick={() => onSetChatMode('nexus')}
      >
        <Network size={14} />
        <span>NEXUS RAG</span>
      </button>
      <button
        className={`mode-toggle-btn ${chatMode === 'mnemosyne' ? 'active' : ''}`}
        onClick={() => onSetChatMode('mnemosyne')}
      >
        <Brain size={14} />
        <span>ZAIA AI</span>
      </button>
    </div>
  );
}

export default ModeToggle;
