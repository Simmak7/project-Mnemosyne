/**
 * ChatCanvas - Center panel with chat messages and input
 *
 * Features:
 * - Message display with streaming support
 * - Citation chips that update ContextRadar preview
 * - Input area with send button
 * - Auto-scroll to latest message
 * - Message actions (copy, regenerate)
 * - Timestamps on messages
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Send,
  Square,
  Bot,
  User,
  AlertCircle,
  Loader2,
  FileText,
  Image as ImageIcon,
  Copy,
  Check,
  RefreshCw,
  Clock,
} from 'lucide-react';
import { useAIChat } from '../hooks/useAIChat';
import { useAIChatContext } from '../hooks/AIChatContext';
import './ChatCanvas.css';

/**
 * Format timestamp for display
 */
function formatMessageTime(timestamp) {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  const now = new Date();
  const isToday = date.toDateString() === now.toDateString();

  if (isToday) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  return date.toLocaleDateString([], { month: 'short', day: 'numeric' }) +
         ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

/**
 * Message bubble component with actions
 */
function MessageBubble({
  message,
  onCitationClick,
  onRegenerate,
  isRegenerating,
  showActions = true,
}) {
  const [copied, setCopied] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  const isUser = message.role === 'user';
  const isError = message.isError;
  const isStreaming = message.isStreaming;

  // Handle copy to clipboard
  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  }, [message.content]);

  // Handle regenerate
  const handleRegenerate = useCallback(() => {
    if (onRegenerate && !isStreaming && !isRegenerating) {
      onRegenerate(message);
    }
  }, [message, onRegenerate, isStreaming, isRegenerating]);

  // Extract citation numbers from content for highlighting
  const citationPattern = /\[(\d+)\]/g;

  // Render content with clickable citations
  const renderContent = () => {
    if (!message.citations || message.citations.length === 0) {
      return <span>{message.content}</span>;
    }

    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = citationPattern.exec(message.content)) !== null) {
      // Add text before citation
      if (match.index > lastIndex) {
        parts.push(
          <span key={`text-${lastIndex}`}>
            {message.content.slice(lastIndex, match.index)}
          </span>
        );
      }

      // Add citation chip
      const citationIndex = parseInt(match[1], 10);
      // Backend returns 'index', not 'citation_index'
      const citation = message.citations?.find(c => c.index === citationIndex);

      parts.push(
        <button
          key={`citation-${match.index}`}
          className="citation-chip"
          onClick={() => onCitationClick(citation)}
          onMouseEnter={() => onCitationClick(citation)}
          title={citation ? `${citation.source_type}: ${citation.title || 'Source'}` : 'Citation'}
        >
          [{citationIndex}]
        </button>
      );

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < message.content.length) {
      parts.push(
        <span key={`text-${lastIndex}`}>
          {message.content.slice(lastIndex)}
        </span>
      );
    }

    return parts;
  };

  return (
    <div
      className={`message-bubble ${isUser ? 'user' : 'assistant'} ${isError ? 'error' : ''}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="message-avatar">
        {isUser ? (
          <User size={18} />
        ) : isError ? (
          <AlertCircle size={18} />
        ) : (
          <Bot size={18} />
        )}
      </div>

      <div className="message-content">
        <div className="message-text">
          {renderContent()}
          {isStreaming && <span className="streaming-cursor" />}
        </div>

        {/* Message footer with timestamp and actions */}
        <div className={`message-footer ${isHovered || copied ? 'visible' : ''}`}>
          {/* Timestamp */}
          {message.timestamp && (
            <span className="message-timestamp">
              <Clock size={10} />
              {formatMessageTime(message.timestamp)}
            </span>
          )}

          {/* Action buttons - show on hover */}
          {showActions && !isStreaming && (
            <div className="message-actions">
              {/* Copy button */}
              <button
                className={`message-action-btn ${copied ? 'copied' : ''}`}
                onClick={handleCopy}
                title={copied ? 'Copied!' : 'Copy message'}
              >
                {copied ? <Check size={14} /> : <Copy size={14} />}
              </button>

              {/* Regenerate button - only for assistant messages */}
              {!isUser && !isError && onRegenerate && (
                <button
                  className={`message-action-btn ${isRegenerating ? 'regenerating' : ''}`}
                  onClick={handleRegenerate}
                  disabled={isRegenerating}
                  title="Regenerate response"
                >
                  <RefreshCw size={14} className={isRegenerating ? 'spinning' : ''} />
                </button>
              )}
            </div>
          )}
        </div>

        {/* Citations summary */}
        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="message-citations">
            <span className="citations-label">Sources:</span>
            <div className="citations-list">
              {message.citations.slice(0, 5).map((citation, idx) => (
                <button
                  key={idx}
                  className={`citation-badge ${citation.source_type}`}
                  onClick={() => onCitationClick(citation)}
                  onMouseEnter={() => onCitationClick(citation)}
                >
                  {citation.source_type === 'note' ? (
                    <FileText size={12} />
                  ) : (
                    <ImageIcon size={12} />
                  )}
                  <span>{citation.title || `${citation.source_type} #${citation.source_id}`}</span>
                </button>
              ))}
              {message.citations.length > 5 && (
                <span className="citations-more">+{message.citations.length - 5} more</span>
              )}
            </div>
          </div>
        )}

        {/* Confidence indicator */}
        {!isUser && message.confidenceLevel && (
          <div className={`message-confidence ${message.confidenceLevel}`}>
            Confidence: {message.confidenceLevel}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Empty state component
 */
function EmptyState() {
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

/**
 * ChatCanvas - Main chat interface
 * Uses forwardRef to expose inputRef for keyboard shortcuts
 */
const ChatCanvas = React.forwardRef(function ChatCanvas(
  { onNavigateToNote, onNavigateToImage, initialQuery, onClearInitialQuery },
  ref
) {
  const [inputValue, setInputValue] = useState('');
  const [regeneratingId, setRegeneratingId] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Expose inputRef to parent for keyboard shortcuts
  React.useImperativeHandle(ref, () => ({
    focusInput: () => {
      if (inputRef.current) {
        inputRef.current.focus();
      }
    },
    getInputRef: () => inputRef.current,
  }));

  const {
    messages,
    isLoading,
    isStreaming,
    sendQuery,
    sendStreamingQuery,
    cancelStream,
    setPreview,
    regenerateMessage,
  } = useAIChat();

  const { settings } = useAIChatContext();

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  // Handle initial query from deep linking (e.g., "Ask AI about this note")
  useEffect(() => {
    if (initialQuery && onClearInitialQuery) {
      // Set the input value
      setInputValue(initialQuery);
      // Focus the input
      if (inputRef.current) {
        inputRef.current.focus();
      }
      // Clear the initial query after consuming
      onClearInitialQuery();
    }
  }, [initialQuery, onClearInitialQuery]);

  // Handle send message
  const handleSend = useCallback(async () => {
    const query = inputValue.trim();
    if (!query || isLoading) return;

    setInputValue('');

    try {
      if (settings.useStreaming) {
        await sendStreamingQuery(query);
      } else {
        await sendQuery(query);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  }, [inputValue, isLoading, settings.useStreaming, sendQuery, sendStreamingQuery]);

  // Handle key press
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  // Handle citation click - update preview in ContextRadar
  const handleCitationClick = useCallback((citation) => {
    if (!citation) return;

    setPreview({
      type: citation.source_type,
      id: citation.source_id,
      title: citation.title,
      citation,
    });
  }, [setPreview]);

  // Handle message regeneration
  const handleRegenerate = useCallback(async (message) => {
    if (!regenerateMessage || isLoading || regeneratingId) return;

    // Find the user message that preceded this assistant message
    const messageIndex = messages.findIndex(m => m.id === message.id);
    if (messageIndex <= 0) return;

    const userMessage = messages[messageIndex - 1];
    if (userMessage.role !== 'user') return;

    setRegeneratingId(message.id);
    try {
      await regenerateMessage(userMessage.content, message.id);
    } catch (error) {
      console.error('Failed to regenerate:', error);
    } finally {
      setRegeneratingId(null);
    }
  }, [messages, regenerateMessage, isLoading, regeneratingId]);

  return (
    <div className="chat-canvas">
      {/* Messages Area */}
      <div className="chat-messages">
        {messages.length === 0 ? (
          <EmptyState />
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                onCitationClick={handleCitationClick}
                onRegenerate={handleRegenerate}
                isRegenerating={regeneratingId === message.id}
              />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="chat-input-area">
        <div className="chat-input-container">
          <textarea
            ref={inputRef}
            className="chat-input"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your notes and images..."
            rows={1}
            disabled={isLoading}
          />

          {isStreaming ? (
            <button
              className="chat-cancel-btn"
              onClick={cancelStream}
              title="Cancel"
            >
              <Square size={18} />
            </button>
          ) : (
            <button
              className="chat-send-btn"
              onClick={handleSend}
              disabled={!inputValue.trim() || isLoading}
              title="Send message"
            >
              {isLoading ? (
                <Loader2 size={18} className="spinning" />
              ) : (
                <Send size={18} />
              )}
            </button>
          )}
        </div>

        <div className="chat-input-hint">
          <kbd>Enter</kbd> to send · <kbd>Shift+Enter</kbd> new line · <kbd>Ctrl+/</kbd> focus · <kbd>Ctrl+N</kbd> new chat
        </div>
      </div>
    </div>
  );
});

export default ChatCanvas;
