import React, { useState, useRef, useEffect } from 'react';
import { X } from 'lucide-react';
import './AIChat.css';

function AIChat({ mode = 'standalone', context = null, onClose }) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const isOverlay = mode === 'overlay';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Get initial context message
  const getInitialMessage = () => {
    if (!context) return '';

    switch (context.type) {
      case 'note':
        return `I'm looking at the note "${context.title}". Here's the content:\n\n${context.content}\n\nWhat can you tell me about this?`;
      case 'tag':
        return `Show me insights about the tag #${context.tagName}`;
      default:
        return '';
    }
  };

  // Auto-send context message on mount
  useEffect(() => {
    if (context && messages.length === 0) {
      const contextMessage = getInitialMessage();
      if (contextMessage) {
        handleSendMessage({ preventDefault: () => {} }, contextMessage);
      }
    }
  }, [context]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSendMessage = async (e, customMessage = null) => {
    e.preventDefault();
    const messageText = customMessage || inputMessage;
    if (messageText.trim() === '') return;

    const newMessage = { text: messageText, sender: 'user' };
    setMessages((prevMessages) => [...prevMessages, newMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setMessages((prevMessages) => [...prevMessages, {
          text: 'Please login first to use AI chat.',
          sender: 'ai'
        }]);
        setLoading(false);
        return;
      }

      const response = await fetch('http://localhost:8000/chat-with-ai/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ text: messageText }),
      });

      if (response.ok) {
        const data = await response.json();
        setMessages((prevMessages) => [...prevMessages, { text: data.response, sender: 'ai' }]);
      } else if (response.status === 401 || response.status === 403) {
        // Token expired, redirect to login
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        window.location.reload();
      } else {
        const errorData = await response.json();
        setMessages((prevMessages) => [...prevMessages, { text: `Error: ${errorData.detail}`, sender: 'ai' }]);
      }
    } catch (error) {
      setMessages((prevMessages) => [...prevMessages, { text: `Error connecting to AI: ${error.message}`, sender: 'ai' }]);
    } finally {
      setLoading(false);
    }
  };

  const wrapperClass = isOverlay
    ? 'ai-chat-overlay-wrapper'
    : 'component-container';

  return (
    <div className={wrapperClass}>
      {isOverlay && (
        <div className="overlay-header">
          <h3>AI Assistant</h3>
          <button onClick={onClose} className="close-btn" aria-label="Close chat">
            <X className="w-5 h-5" />
          </button>
        </div>
      )}

      {!isOverlay && <h2>Chat with AI</h2>}

      <div className="chat-window">
        <div className="messages-display">
          {messages.length === 0 && (
            <p className="no-messages">
              {context ? 'AI is analyzing your content...' : 'Start a conversation with the AI!'}
            </p>
          )}
          {messages.map((msg, index) => (
            <div key={index} className={`message-bubble ${msg.sender}`}>
              {msg.text}
            </div>
          ))}
          {loading && (
            <div className="message-bubble ai loading-bubble">
              <div className="loading"></div>
              <span>AI is thinking...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        <form onSubmit={handleSendMessage} className="message-input-form">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Type your message..."
            disabled={loading}
          />
          <button type="submit" disabled={loading}>Send</button>
        </form>
      </div>
    </div>
  );
}

export default AIChat;

