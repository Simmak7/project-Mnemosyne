import React from 'react';
import { Send, Square, Loader2 } from 'lucide-react';

/**
 * Chat input area with send button
 */
function ChatInput({
  inputRef,
  inputValue,
  setInputValue,
  isLoading,
  isStreaming,
  isBrainMode,
  onSend,
  onCancel,
  onKeyDown,
}) {
  return (
    <div className="chat-input-area">
      <div className="chat-input-container">
        <textarea
          ref={inputRef}
          className="chat-input"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder={isBrainMode
            ? "Ask ZAIA AI about your knowledge..."
            : "Ask about your notes and images..."
          }
          rows={1}
          disabled={isLoading}
        />

        {isStreaming ? (
          <button
            className="chat-cancel-btn"
            onClick={onCancel}
            title="Cancel"
          >
            <Square size={18} />
          </button>
        ) : (
          <button
            className="chat-send-btn"
            onClick={onSend}
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
  );
}

export default React.memo(ChatInput);
