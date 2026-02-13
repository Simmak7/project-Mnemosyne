import React from 'react';
import { Bot } from 'lucide-react';

/**
 * Empty state component for chat canvas
 */
function EmptyState({ isBrainMode }) {
  if (isBrainMode) {
    return (
      <div className="chat-empty-state">
        <Bot size={48} className="empty-icon brain-mode" />
        <h3>ZAIA AI</h3>
        <p>
          I have deep knowledge of your notes. Ask me anything and I'll draw
          connections across topics with a personal touch — no citations needed.
        </p>
        <div className="empty-suggestions">
          <span className="suggestion-label">Try asking:</span>
          <div className="suggestions-list">
            <button className="suggestion-chip">"What patterns do you see in my notes?"</button>
            <button className="suggestion-chip">"Connect my ideas about..."</button>
            <button className="suggestion-chip">"What are my main interests?"</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-empty-state">
      <Bot size={48} className="empty-icon" />
      <h3>Start a conversation</h3>
      <p>
        Ask me about your notes, images, or anything in your knowledge base.
        I'll search through your content and provide relevant answers with sources.
      </p>
      <div className="empty-suggestions">
        <span className="suggestion-label">Try asking:</span>
        <div className="suggestions-list">
          <button className="suggestion-chip">"What do I know about..."</button>
          <button className="suggestion-chip">"Summarize my notes on..."</button>
          <button className="suggestion-chip">"Find images related to..."</button>
        </div>
      </div>
    </div>
  );
}

export default React.memo(EmptyState);
