/**
 * RAGChat - Citation-aware AI Chat Component
 *
 * Features:
 * - Multi-turn conversations with context
 * - Real-time streaming responses
 * - Source citations with explainability
 * - Conversation history management
 * - Keyboard shortcuts
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Send,
  X,
  Loader2,
  StopCircle,
  Trash2,
  MessageSquare,
  Plus,
  ChevronRight,
  Info,
  BookOpen,
} from 'lucide-react';
import useRAGChat from '../../hooks/useRAGChat';
import { CitationList } from './CitationCard';
import RetrievalExplainer, { RetrievalBadges } from './RetrievalExplainer';
import './RAGChat.css';

/**
 * Format citation markers in text to be clickable
 */
const formatMessageWithCitations = (content, citations, onCitationClick) => {
  if (!content || !citations || citations.length === 0) {
    return content;
  }

  // Split by citation patterns [N]
  const parts = content.split(/(\[\d+\])/g);

  return parts.map((part, idx) => {
    const match = part.match(/\[(\d+)\]/);
    if (match) {
      const citationIndex = parseInt(match[1], 10);
      const citation = citations.find(c => c.index === citationIndex);
      if (citation) {
        return (
          <button
            key={idx}
            className="inline-citation"
            onClick={() => onCitationClick?.(citation)}
            title={citation.title}
          >
            [{citationIndex}]
          </button>
        );
      }
    }
    return <span key={idx}>{part}</span>;
  });
};

/**
 * Message component
 */
function Message({
  message,
  onCitationClick,
  onNavigate,
  showCitations = true,
}) {
  const [showAllCitations, setShowAllCitations] = useState(false);

  const isUser = message.role === 'user';
  const hasCitations = message.citations && message.citations.length > 0;

  return (
    <div className={`rag-message ${isUser ? 'user' : 'assistant'} ${message.isError ? 'error' : ''}`}>
      {/* Message content */}
      <div className="message-content">
        {message.isStreaming ? (
          <>
            {message.content}
            <span className="streaming-cursor" />
          </>
        ) : isUser ? (
          message.content
        ) : (
          formatMessageWithCitations(message.content, message.citations, onCitationClick)
        )}
      </div>

      {/* Assistant message extras */}
      {!isUser && !message.isError && !message.isStreaming && (
        <div className="message-extras">
          {/* Confidence and metadata badges */}
          {message.confidenceLevel && (
            <RetrievalBadges
              metadata={{ retrieval_methods_used: [], sources_used: message.citations?.length || 0 }}
              confidenceLevel={message.confidenceLevel}
            />
          )}

          {/* Citations toggle */}
          {hasCitations && showCitations && (
            <button
              className="citations-toggle"
              onClick={() => setShowAllCitations(!showAllCitations)}
            >
              <BookOpen size={14} />
              <span>
                {showAllCitations ? 'Hide' : 'Show'} {message.citations.length} sources
              </span>
              <ChevronRight
                size={14}
                className={showAllCitations ? 'rotated' : ''}
              />
            </button>
          )}

          {/* Expanded citations */}
          {showAllCitations && hasCitations && (
            <div className="message-citations">
              <CitationList
                citations={message.citations}
                usedIndices={message.usedCitationIndices || []}
                onNavigate={onNavigate}
                showUnused={true}
              />
            </div>
          )}
        </div>
      )}

      {/* Timestamp */}
      <div className="message-time">
        {new Date(message.timestamp).toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        })}
      </div>
    </div>
  );
}

/**
 * Empty state component
 */
function EmptyState() {
  return (
    <div className="rag-empty-state">
      <MessageSquare size={48} strokeWidth={1.5} />
      <h3>Ask about your notes</h3>
      <p>
        I can answer questions using information from your notes and images.
        I'll cite my sources so you can verify the information.
      </p>
      <div className="example-queries">
        <p className="examples-label">Try asking:</p>
        <ul>
          <li>"What are the key concepts in my machine learning notes?"</li>
          <li>"How do the topics in my project notes connect?"</li>
          <li>"What images do I have related to architecture?"</li>
        </ul>
      </div>
    </div>
  );
}

/**
 * RAGChat main component
 */
function RAGChat({
  mode = 'standalone',
  onClose,
  onNavigateToNote,
  onNavigateToImage,
  initialQuery = '',
  className = '',
}) {
  const [inputValue, setInputValue] = useState(initialQuery);
  const [useStreaming, setUseStreaming] = useState(true);
  const [selectedCitation, setSelectedCitation] = useState(null);
  const [showExplainer, setShowExplainer] = useState(false);

  const inputRef = useRef(null);
  const messagesEndRef = useRef(null);

  const {
    messages,
    isLoading,
    isStreaming,
    error,
    lastRetrievalMetadata,
    sendQuery,
    sendStreamingQuery,
    cancelStream,
    clearMessages,
  } = useRAGChat();

  const isOverlay = mode === 'overlay';

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Handle send
  const handleSend = useCallback(async () => {
    if (!inputValue.trim() || isLoading) return;

    const query = inputValue.trim();
    setInputValue('');

    try {
      if (useStreaming) {
        await sendStreamingQuery(query);
      } else {
        await sendQuery(query);
      }
    } catch (err) {
      console.error('Query failed:', err);
    }
  }, [inputValue, isLoading, useStreaming, sendQuery, sendStreamingQuery]);

  // Handle key press
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Handle citation click
  const handleCitationClick = (citation) => {
    setSelectedCitation(citation);
  };

  // Handle navigation to source
  const handleNavigate = (sourceType, sourceId) => {
    if (sourceType === 'note' || sourceType === 'chunk') {
      onNavigateToNote?.(sourceId);
    } else if (sourceType === 'image') {
      onNavigateToImage?.(sourceId);
    }
    setSelectedCitation(null);
  };

  // Close citation panel
  const closeCitationPanel = () => {
    setSelectedCitation(null);
  };

  return (
    <div className={`rag-chat ${isOverlay ? 'overlay-mode' : ''} ${className}`}>
      {/* Header */}
      <div className="rag-chat-header">
        <div className="header-title">
          <MessageSquare size={20} />
          <h3>Ask Your Notes</h3>
        </div>
        <div className="header-actions">
          {messages.length > 0 && (
            <>
              <button
                className="header-btn"
                onClick={() => setShowExplainer(!showExplainer)}
                title="Show how answers are generated"
              >
                <Info size={18} />
              </button>
              <button
                className="header-btn"
                onClick={clearMessages}
                title="Clear conversation"
              >
                <Trash2 size={18} />
              </button>
            </>
          )}
          {isOverlay && onClose && (
            <button
              className="header-btn close"
              onClick={onClose}
              aria-label="Close chat"
            >
              <X size={20} />
            </button>
          )}
        </div>
      </div>

      {/* Explainer panel */}
      {showExplainer && lastRetrievalMetadata && (
        <div className="rag-explainer-panel">
          <RetrievalExplainer
            metadata={lastRetrievalMetadata}
            confidenceScore={messages[messages.length - 1]?.confidenceScore}
            confidenceLevel={messages[messages.length - 1]?.confidenceLevel}
            isCollapsible={false}
          />
        </div>
      )}

      {/* Messages area */}
      <div className="rag-messages">
        {messages.length === 0 ? (
          <EmptyState />
        ) : (
          messages.map((message) => (
            <Message
              key={message.id}
              message={message}
              onCitationClick={handleCitationClick}
              onNavigate={handleNavigate}
            />
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Citation detail panel */}
      {selectedCitation && (
        <div className="citation-detail-panel">
          <div className="panel-header">
            <h4>Source [{selectedCitation.index}]</h4>
            <button onClick={closeCitationPanel}>
              <X size={16} />
            </button>
          </div>
          <div className="panel-content">
            <h5>{selectedCitation.title}</h5>
            <p className="citation-preview">{selectedCitation.content_preview}</p>
            <button
              className="navigate-btn"
              onClick={() => handleNavigate(selectedCitation.source_type, selectedCitation.source_id)}
            >
              Open {selectedCitation.source_type}
            </button>
          </div>
        </div>
      )}

      {/* Input area */}
      <div className="rag-input-area">
        {isStreaming && (
          <button
            className="cancel-stream-btn"
            onClick={cancelStream}
          >
            <StopCircle size={16} />
            Stop generating
          </button>
        )}
        <div className="input-container">
          <textarea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your notes..."
            disabled={isLoading}
            rows={1}
          />
          <button
            className="send-btn"
            onClick={handleSend}
            disabled={!inputValue.trim() || isLoading}
            aria-label="Send message"
          >
            {isLoading ? (
              <Loader2 size={20} className="spinning" />
            ) : (
              <Send size={20} />
            )}
          </button>
        </div>
        <div className="input-hint">
          Press Enter to send, Shift+Enter for new line
        </div>
      </div>
    </div>
  );
}

export default RAGChat;
