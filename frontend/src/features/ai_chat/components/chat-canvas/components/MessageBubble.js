import React, { useState, useCallback } from 'react';
import {
  Bot,
  User,
  AlertCircle,
  FileText,
  Image as ImageIcon,
  Copy,
  Check,
  RefreshCw,
  Clock,
} from 'lucide-react';
import { formatMessageTime } from '../utils';

/**
 * Message bubble component with actions
 */
function MessageBubble({
  message,
  onCitationClick,
  onCitationDoubleClick,
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
      if (match.index > lastIndex) {
        parts.push(
          <span key={`text-${lastIndex}`}>
            {message.content.slice(lastIndex, match.index)}
          </span>
        );
      }

      const citationIndex = parseInt(match[1], 10);
      const citation = message.citations?.find(c => c.index === citationIndex);

      parts.push(
        <button
          key={`citation-${match.index}`}
          className="citation-chip"
          onClick={() => onCitationClick(citation)}
          onMouseEnter={() => onCitationClick(citation)}
          onDoubleClick={(e) => {
            e.preventDefault();
            if (onCitationDoubleClick) onCitationDoubleClick(citation);
          }}
          title={citation ? `[${citationIndex}] ${citation.title || 'Source'} — double-click to insert` : 'Citation'}
        >
          [{citationIndex}]
        </button>
      );

      lastIndex = match.index + match[0].length;
    }

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

        <MessageFooter
          message={message}
          isHovered={isHovered}
          copied={copied}
          isUser={isUser}
          isError={isError}
          isStreaming={isStreaming}
          isRegenerating={isRegenerating}
          showActions={showActions}
          onCopy={handleCopy}
          onRegenerate={handleRegenerate}
        />

        <MessageCitations
          message={message}
          isUser={isUser}
          onCitationClick={onCitationClick}
        />

        <MessageMeta message={message} isUser={isUser} />
      </div>
    </div>
  );
}

/**
 * Message footer with timestamp and actions
 */
function MessageFooter({
  message,
  isHovered,
  copied,
  isUser,
  isError,
  isStreaming,
  isRegenerating,
  showActions,
  onCopy,
  onRegenerate,
}) {
  return (
    <div className={`message-footer ${isHovered || copied ? 'visible' : ''}`}>
      {message.timestamp && (
        <span className="message-timestamp">
          <Clock size={10} />
          {formatMessageTime(message.timestamp)}
        </span>
      )}

      {showActions && !isStreaming && (
        <div className="message-actions">
          <button
            className={`message-action-btn ${copied ? 'copied' : ''}`}
            onClick={onCopy}
            title={copied ? 'Copied!' : 'Copy message'}
          >
            {copied ? <Check size={14} /> : <Copy size={14} />}
          </button>

          {!isUser && !isError && onRegenerate && (
            <button
              className={`message-action-btn ${isRegenerating ? 'regenerating' : ''}`}
              onClick={onRegenerate}
              disabled={isRegenerating}
              title="Regenerate response"
            >
              <RefreshCw size={14} className={isRegenerating ? 'spinning' : ''} />
            </button>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Citations display for RAG and Brain modes
 */
function MessageCitations({ message, isUser, onCitationClick }) {
  // RAG mode citations
  if (!isUser && !message.isBrainMode && message.citations && message.citations.length > 0) {
    return (
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
    );
  }

  // Brain mode topics
  if (!isUser && message.isBrainMode && message.topicsMatched && message.topicsMatched.length > 0) {
    return (
      <div className="message-citations">
        <span className="citations-label">Topics:</span>
        <div className="citations-list">
          {message.topicsMatched.map((topic, idx) => (
            <span key={idx} className="citation-badge brain-topic">
              <FileText size={12} />
              <span>{typeof topic === 'string' ? topic : topic.title || topic.key}</span>
            </span>
          ))}
        </div>
      </div>
    );
  }

  return null;
}

/**
 * Message metadata (confidence, model used)
 */
function MessageMeta({ message, isUser }) {
  return (
    <>
      {!isUser && message.brainIsStale && (
        <div className="message-brain-stale">
          <AlertCircle size={12} />
          <span>Brain knowledge is outdated - rebuild recommended</span>
        </div>
      )}

      {!isUser && !message.isBrainMode && message.confidenceLevel && (
        <div className={`message-confidence ${message.confidenceLevel}`}>
          Confidence: {message.confidenceLevel}
        </div>
      )}

      {!isUser && message.modelUsed && (
        <div className="message-model-used">
          <Bot size={10} />
          <span>{message.modelUsed}</span>
        </div>
      )}
    </>
  );
}

export default React.memo(MessageBubble);
