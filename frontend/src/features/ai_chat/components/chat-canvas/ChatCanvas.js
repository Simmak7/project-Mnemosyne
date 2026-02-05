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

import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { useAIChat } from '../../hooks/useAIChat';
import { useAIChatContext } from '../../hooks/AIChatContext';
import { EmptyState, MessageBubble, ChatInput } from './components';
import '../ChatCanvas.css';

/**
 * ChatCanvas - Main chat interface
 * Uses forwardRef to expose inputRef for keyboard shortcuts
 */
// Threshold for switching to virtualized rendering
const VIRTUALIZATION_THRESHOLD = 50;

const ChatCanvas = React.forwardRef(function ChatCanvas(
  { onNavigateToNote, onNavigateToImage, initialQuery, onClearInitialQuery },
  ref
) {
  const [inputValue, setInputValue] = useState('');
  const [regeneratingId, setRegeneratingId] = useState(null);
  const messagesContainerRef = useRef(null);
  const inputRef = useRef(null);
  const shouldAutoScroll = useRef(true);

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

  const { settings, state: chatState } = useAIChatContext();
  const isBrainMode = chatState.chatMode === 'mnemosyne';

  // Determine if we should use virtualization (for large message lists)
  const useVirtualization = messages.length >= VIRTUALIZATION_THRESHOLD;

  // Virtualizer for large message lists
  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => messagesContainerRef.current,
    estimateSize: () => 120, // Estimated message height
    overscan: 5,
    enabled: useVirtualization,
  });

  // Track scroll position to determine if user is near bottom
  const handleScroll = useCallback(() => {
    if (!messagesContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current;
    // User is near bottom if within 100px
    shouldAutoScroll.current = scrollHeight - scrollTop - clientHeight < 100;
  }, []);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (!shouldAutoScroll.current) return;

    if (useVirtualization && virtualizer) {
      // For virtualized list, scroll to last item
      virtualizer.scrollToIndex(messages.length - 1, { align: 'end', behavior: 'smooth' });
    } else if (messagesContainerRef.current) {
      // For non-virtualized, scroll container to bottom
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  }, [messages, useVirtualization, virtualizer]);

  // Focus input on mount
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  // Handle initial query from deep linking
  useEffect(() => {
    if (initialQuery && onClearInitialQuery) {
      setInputValue(initialQuery);
      if (inputRef.current) {
        inputRef.current.focus();
      }
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

  // Render messages - virtualized for large lists, regular for small
  const renderMessages = () => {
    if (messages.length === 0) {
      return <EmptyState isBrainMode={isBrainMode} />;
    }

    // Use virtualization for large message lists (50+ messages)
    if (useVirtualization) {
      const virtualItems = virtualizer.getVirtualItems();

      return (
        <div
          style={{
            height: `${virtualizer.getTotalSize()}px`,
            width: '100%',
            position: 'relative',
          }}
        >
          {virtualItems.map((virtualItem) => {
            const message = messages[virtualItem.index];
            return (
              <div
                key={virtualItem.key}
                data-index={virtualItem.index}
                ref={virtualizer.measureElement}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  transform: `translateY(${virtualItem.start}px)`,
                }}
              >
                <MessageBubble
                  message={message}
                  onCitationClick={handleCitationClick}
                  onRegenerate={handleRegenerate}
                  isRegenerating={regeneratingId === message.id}
                />
              </div>
            );
          })}
        </div>
      );
    }

    // Regular rendering for small message lists
    return messages.map((message) => (
      <MessageBubble
        key={message.id}
        message={message}
        onCitationClick={handleCitationClick}
        onRegenerate={handleRegenerate}
        isRegenerating={regeneratingId === message.id}
      />
    ));
  };

  return (
    <div className="chat-canvas">
      {/* Messages Area */}
      <div
        className="chat-messages"
        ref={messagesContainerRef}
        onScroll={handleScroll}
      >
        {renderMessages()}
      </div>

      {/* Input Area */}
      <ChatInput
        inputRef={inputRef}
        inputValue={inputValue}
        setInputValue={setInputValue}
        isLoading={isLoading}
        isStreaming={isStreaming}
        isBrainMode={isBrainMode}
        onSend={handleSend}
        onCancel={cancelStream}
        onKeyDown={handleKeyDown}
      />
    </div>
  );
});

export default ChatCanvas;
