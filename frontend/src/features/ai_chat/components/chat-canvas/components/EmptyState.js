import React, { useMemo } from 'react';
import { Bot, Network, Brain, Search } from 'lucide-react';

/**
 * Suggestions per chat mode, contextual to the mode's purpose.
 */
const SUGGESTIONS = {
  nexus: [
    'What are my most connected topics?',
    'Summarize my recent notes',
    'Find links between my ideas',
  ],
  mnemosyne: [
    'What patterns do you see in my thinking?',
    'What topics am I most interested in?',
    'Surprise me with an insight',
  ],
  rag: [
    'Search my notes about...',
    'What images relate to...',
    'Find documents about...',
  ],
};

const MODE_CONFIG = {
  nexus: {
    icon: Network,
    title: 'NEXUS RAG',
    description:
      'I search your notes and images, weaving connections across your entire knowledge base. Ask anything and I will find the most relevant sources.',
  },
  mnemosyne: {
    icon: Brain,
    title: 'ZAIA AI',
    description:
      'I have deep knowledge of your notes. Ask me anything and I will draw connections across topics with a personal touch -- no citations needed.',
  },
  rag: {
    icon: Search,
    title: 'Start a conversation',
    description:
      'Ask me about your notes, images, or anything in your knowledge base. I will search through your content and provide relevant answers with sources.',
  },
};

/**
 * Empty state component for chat canvas.
 * Shows mode-specific icon, description, and clickable suggestion chips.
 */
function EmptyState({ chatMode, onSuggestionClick }) {
  const mode = chatMode === 'mnemosyne' ? 'mnemosyne'
    : chatMode === 'rag' ? 'rag' : 'nexus';

  const config = MODE_CONFIG[mode] || MODE_CONFIG.nexus;
  const suggestions = SUGGESTIONS[mode] || SUGGESTIONS.nexus;
  const IconComponent = config.icon;
  const isBrainMode = mode === 'mnemosyne';

  const handleChipClick = useMemo(() => {
    if (!onSuggestionClick) return () => {};
    return (text) => onSuggestionClick(text);
  }, [onSuggestionClick]);

  return (
    <div className="chat-empty-state">
      <IconComponent
        size={48}
        className={`empty-icon ${isBrainMode ? 'brain-mode' : ''}`}
      />
      <h3>{config.title}</h3>
      <p>{config.description}</p>

      <div className="empty-suggestions">
        <span className="suggestion-label">Try asking:</span>
        <div className="suggestions-list">
          {suggestions.map((text) => (
            <button
              key={text}
              className="suggestion-chip"
              onClick={() => handleChipClick(text)}
              type="button"
              aria-label={`Suggest: ${text}`}
            >
              {text}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export default React.memo(EmptyState);
