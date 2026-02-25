/**
 * useRAGChat - Hook for RAG (Retrieval-Augmented Generation) chat API
 *
 * Provides:
 * - Stateless and conversation-based RAG queries
 * - SSE streaming support
 * - Citation tracking and display
 * - Conversation management
 */

import { useState, useCallback, useRef } from 'react';
import { API_URL as API_BASE } from '../../../utils/api';

/**
 * Get auth headers for API requests
 */
const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    'Authorization': token ? `Bearer ${token}` : '',
  };
};

/**
 * Hook for RAG chat functionality
 */
export function useRAGChat() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState(null);
  const [conversationId, setConversationId] = useState(null);
  const [lastRetrievalMetadata, setLastRetrievalMetadata] = useState(null);
  const abortControllerRef = useRef(null);

  /**
   * Send a RAG query (non-streaming)
   */
  const sendQuery = useCallback(async (query, options = {}) => {
    setIsLoading(true);
    setError(null);

    // Add user message
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: query,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await fetch(`${API_BASE}/rag/query`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          query,
          conversation_id: conversationId,
          max_sources: options.maxSources || 10,
          include_images: options.includeImages !== false,
          include_graph: options.includeGraph !== false,
          min_similarity: options.minSimilarity || 0.5,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Request failed: ${response.status}`);
      }

      const data = await response.json();

      // Add assistant message with citations
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.answer,
        citations: data.citations,
        usedCitationIndices: data.used_citation_indices,
        confidenceScore: data.confidence_score,
        confidenceLevel: data.confidence_level,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, assistantMessage]);

      // Update conversation ID if created
      if (data.conversation_id) {
        setConversationId(data.conversation_id);
      }

      // Store retrieval metadata
      setLastRetrievalMetadata(data.retrieval_metadata);

      return data;
    } catch (err) {
      setError(err.message);

      // Add error message
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `Error: ${err.message}`,
        isError: true,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);

      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [conversationId]);

  /**
   * Send a streaming RAG query
   */
  const sendStreamingQuery = useCallback(async (query, options = {}) => {
    setIsLoading(true);
    setIsStreaming(true);
    setError(null);

    // Add user message
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: query,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);

    // Create placeholder for assistant message
    const assistantMessageId = Date.now() + 1;
    const assistantMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      citations: [],
      usedCitationIndices: [],
      isStreaming: true,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, assistantMessage]);

    // Create abort controller
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(`${API_BASE}/rag/query/stream`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          query,
          conversation_id: conversationId,
          max_sources: options.maxSources || 10,
          include_images: options.includeImages !== false,
          include_graph: options.includeGraph !== false,
          min_similarity: options.minSimilarity || 0.5,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedContent = '';
      let citations = [];
      let usedIndices = [];
      let metadata = null;
      let confidence = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              switch (data.type) {
                case 'token':
                  accumulatedContent += data.content;
                  // Update message content
                  setMessages(prev => prev.map(msg =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: accumulatedContent }
                      : msg
                  ));
                  break;

                case 'citations':
                  citations = data.citations;
                  usedIndices = data.used_indices;
                  break;

                case 'metadata':
                  metadata = data.metadata;
                  confidence = {
                    score: data.metadata.confidence_score,
                    level: data.metadata.confidence_level,
                  };
                  setLastRetrievalMetadata(data.metadata);
                  break;

                case 'error':
                  throw new Error(data.content);

                case 'done':
                  // Finalize message
                  setMessages(prev => prev.map(msg =>
                    msg.id === assistantMessageId
                      ? {
                          ...msg,
                          content: accumulatedContent,
                          citations,
                          usedCitationIndices: usedIndices,
                          confidenceScore: confidence?.score,
                          confidenceLevel: confidence?.level,
                          isStreaming: false,
                        }
                      : msg
                  ));
                  break;
              }
            } catch (parseError) {
              console.warn('Failed to parse SSE data:', parseError);
            }
          }
        }
      }

      return { content: accumulatedContent, citations, metadata };
    } catch (err) {
      if (err.name === 'AbortError') {
        // Stream was cancelled
        setMessages(prev => prev.map(msg =>
          msg.id === assistantMessageId
            ? { ...msg, content: msg.content + ' [Cancelled]', isStreaming: false }
            : msg
        ));
        return null;
      }

      setError(err.message);

      // Update message with error
      setMessages(prev => prev.map(msg =>
        msg.id === assistantMessageId
          ? { ...msg, content: `Error: ${err.message}`, isError: true, isStreaming: false }
          : msg
      ));

      throw err;
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  }, [conversationId]);

  /**
   * Cancel streaming query
   */
  const cancelStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  /**
   * Clear chat history
   */
  const clearMessages = useCallback(() => {
    setMessages([]);
    setConversationId(null);
    setLastRetrievalMetadata(null);
    setError(null);
  }, []);

  /**
   * Start a new conversation
   */
  const startNewConversation = useCallback(async (title = null) => {
    try {
      const response = await fetch(`${API_BASE}/rag/conversations`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ title }),
      });

      if (!response.ok) {
        throw new Error('Failed to create conversation');
      }

      const data = await response.json();
      setConversationId(data.id);
      setMessages([]);
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  /**
   * Load an existing conversation
   */
  const loadConversation = useCallback(async (id) => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/rag/conversations/${id}`, {
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error('Failed to load conversation');
      }

      const data = await response.json();
      setConversationId(data.id);

      // Convert messages to our format
      const formattedMessages = data.messages.map(msg => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        citations: msg.citations || [],
        confidenceScore: msg.confidence_score,
        timestamp: msg.created_at,
      }));

      setMessages(formattedMessages);
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * List all conversations
   */
  const listConversations = useCallback(async (skip = 0, limit = 20) => {
    try {
      const response = await fetch(
        `${API_BASE}/rag/conversations?skip=${skip}&limit=${limit}`,
        { headers: getAuthHeaders() }
      );

      if (!response.ok) {
        throw new Error('Failed to list conversations');
      }

      return await response.json();
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  /**
   * Delete a conversation
   */
  const deleteConversation = useCallback(async (id) => {
    try {
      const response = await fetch(`${API_BASE}/rag/conversations/${id}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error('Failed to delete conversation');
      }

      // Clear if it's the current conversation
      if (id === conversationId) {
        setConversationId(null);
        setMessages([]);
      }

      return true;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [conversationId]);

  return {
    // State
    messages,
    isLoading,
    isStreaming,
    error,
    conversationId,
    lastRetrievalMetadata,

    // Query methods
    sendQuery,
    sendStreamingQuery,
    cancelStream,

    // Message management
    clearMessages,
    setMessages,

    // Conversation management
    startNewConversation,
    loadConversation,
    listConversations,
    deleteConversation,
  };
}

export default useRAGChat;
