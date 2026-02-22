/**
 * ChatCanvas - Center panel: messages + input with virtualization and streaming.
 */
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { useAIChat } from '../../hooks/useAIChat';
import { useAIChatContext } from '../../hooks/AIChatContext';
import { EmptyState, MessageBubble, ChatInput } from './components';
import '../ChatCanvas.css';

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

  React.useImperativeHandle(ref, () => ({
    focusInput: () => inputRef.current?.focus(),
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

  const useVirtualization = messages.length >= VIRTUALIZATION_THRESHOLD;
  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => messagesContainerRef.current,
    estimateSize: () => 120, // Estimated message height
    overscan: 5,
    enabled: useVirtualization,
  });

  const handleScroll = useCallback(() => {
    if (!messagesContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current;
    shouldAutoScroll.current = scrollHeight - scrollTop - clientHeight < 100;
  }, []);

  useEffect(() => {
    if (!shouldAutoScroll.current) return;

    if (useVirtualization && virtualizer) {
      virtualizer.scrollToIndex(messages.length - 1, { align: 'end', behavior: 'smooth' });
    } else if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  }, [messages, useVirtualization, virtualizer]);

  useEffect(() => { inputRef.current?.focus(); }, []);

  useEffect(() => {
    if (initialQuery && onClearInitialQuery) {
      setInputValue(initialQuery);
      inputRef.current?.focus();
      onClearInitialQuery();
    }
  }, [initialQuery, onClearInitialQuery]);

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

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  const handleCitationClick = useCallback((citation) => {
    if (!citation) return;

    setPreview({
      type: citation.source_type,
      id: citation.source_id,
      title: citation.title,
      citation,
    });
  }, [setPreview]);

  const handleCitationDoubleClick = useCallback((citation) => {
    if (!citation?.title) return;
    const mention = `"${citation.title}" `;
    setInputValue(prev => {
      if (!prev.trim()) return mention;
      return prev.trimEnd() + ' ' + mention;
    });
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  const handleSuggestionClick = useCallback(async (text) => {
    if (!text || isLoading) return;
    setInputValue('');
    try {
      if (settings.useStreaming) {
        await sendStreamingQuery(text);
      } else {
        await sendQuery(text);
      }
    } catch (error) {
      console.error('Failed to send suggestion:', error);
    }
  }, [isLoading, settings.useStreaming, sendQuery, sendStreamingQuery]);

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

  const renderMessages = () => {
    if (messages.length === 0) {
      return (
        <EmptyState
          chatMode={chatState.chatMode}
          onSuggestionClick={handleSuggestionClick}
        />
      );
    }

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
                  onCitationDoubleClick={handleCitationDoubleClick}
                  onRegenerate={handleRegenerate}
                  isRegenerating={regeneratingId === message.id}
                />
              </div>
            );
          })}
        </div>
      );
    }

    return messages.map((message) => (
      <MessageBubble
        key={message.id}
        message={message}
        onCitationClick={handleCitationClick}
        onCitationDoubleClick={handleCitationDoubleClick}
        onRegenerate={handleRegenerate}
        isRegenerating={regeneratingId === message.id}
      />
    ));
  };

  return (
    <div className="chat-canvas">
      <div
        className="chat-messages"
        ref={messagesContainerRef}
        onScroll={handleScroll}
      >
        {renderMessages()}
      </div>

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
