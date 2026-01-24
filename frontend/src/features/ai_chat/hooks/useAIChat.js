/**
 * useAIChat - Hook for AI Chat API operations
 *
 * Uses AIChatContext for persistent state.
 * Provides query methods, conversation management, and streaming support.
 */

import { useCallback, useRef } from 'react';
import { useAIChatContext, useAIChatActions } from './AIChatContext';

const API_BASE = 'http://localhost:8000';

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
 * Hook for AI chat functionality
 */
export function useAIChat() {
  const { state, settings } = useAIChatContext();
  const actions = useAIChatActions();
  const abortControllerRef = useRef(null);

  /**
   * Send a RAG query (non-streaming)
   */
  const sendQuery = useCallback(async (query, options = {}) => {
    actions.setLoading(true);
    actions.setError(null);

    // Add user message
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: query,
      timestamp: new Date().toISOString(),
    };
    actions.addMessage(userMessage);

    try {
      const response = await fetch(`${API_BASE}/rag/query`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          query,
          conversation_id: state.conversationId,
          max_sources: options.maxSources ?? settings.maxSources,
          include_images: options.includeImages ?? settings.includeImages,
          include_graph: options.includeGraph ?? settings.includeGraph,
          min_similarity: options.minSimilarity ?? settings.minSimilarity,
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
      actions.addMessage(assistantMessage);

      // Update conversation ID if created (including auto-created)
      if (data.conversation_id && data.conversation_id !== state.conversationId) {
        actions.setConversation(data.conversation_id);
      }

      // Store retrieval metadata
      actions.setRetrievalMetadata(data.retrieval_metadata);

      // Set active citations and auto-preview the most relevant one
      if (data.citations && data.citations.length > 0) {
        actions.setActiveCitations(data.citations);
        // Auto-preview the most relevant citation
        const topCitation = data.citations[0];
        actions.setPreview({
          type: topCitation.source_type,
          id: topCitation.source_id,
          title: topCitation.title,
          citation: topCitation,
        });
      }

      return data;
    } catch (err) {
      actions.setError(err.message);

      // Add error message
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `Error: ${err.message}`,
        isError: true,
        timestamp: new Date().toISOString(),
      };
      actions.addMessage(errorMessage);

      throw err;
    } finally {
      actions.setLoading(false);
    }
  }, [state.conversationId, settings, actions]);

  /**
   * Send a streaming RAG query
   */
  const sendStreamingQuery = useCallback(async (query, options = {}) => {
    actions.setLoading(true);
    actions.setStreaming(true);
    actions.setError(null);

    // Add user message
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: query,
      timestamp: new Date().toISOString(),
    };
    actions.addMessage(userMessage);

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
    actions.addMessage(assistantMessage);

    // Create abort controller
    abortControllerRef.current = new AbortController();

    // Track accumulated content outside try block for use in catch
    let accumulatedContent = '';

    try {
      const response = await fetch(`${API_BASE}/rag/query/stream`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          query,
          conversation_id: state.conversationId,
          max_sources: options.maxSources ?? settings.maxSources,
          include_images: options.includeImages ?? settings.includeImages,
          include_graph: options.includeGraph ?? settings.includeGraph,
          min_similarity: options.minSimilarity ?? settings.minSimilarity,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let citations = [];
      let usedIndices = [];
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
                  actions.updateMessage(assistantMessageId, { content: accumulatedContent });
                  break;

                case 'citations':
                  citations = data.citations;
                  usedIndices = data.used_indices;
                  break;

                case 'metadata':
                  confidence = {
                    score: data.metadata.confidence_score,
                    level: data.metadata.confidence_level,
                  };
                  actions.setRetrievalMetadata(data.metadata);
                  // Always update conversation ID from server (handles auto-create and cross-user scenarios)
                  if (data.metadata.conversation_id && data.metadata.conversation_id !== state.conversationId) {
                    actions.setConversation(data.metadata.conversation_id);
                  }
                  break;

                case 'error':
                  throw new Error(data.content);

                case 'done':
                  actions.updateMessage(assistantMessageId, {
                    content: accumulatedContent,
                    citations,
                    usedCitationIndices: usedIndices,
                    confidenceScore: confidence?.score,
                    confidenceLevel: confidence?.level,
                    isStreaming: false,
                  });
                  // Set active citations and auto-preview the most relevant one
                  if (citations && citations.length > 0) {
                    actions.setActiveCitations(citations);
                    // Auto-preview the most relevant citation
                    const topCitation = citations[0];
                    actions.setPreview({
                      type: topCitation.source_type,
                      id: topCitation.source_id,
                      title: topCitation.title,
                      citation: topCitation,
                    });
                  }
                  break;
              }
            } catch (parseError) {
              console.warn('Failed to parse SSE data:', parseError);
            }
          }
        }
      }

      return { content: accumulatedContent, citations };
    } catch (err) {
      if (err.name === 'AbortError') {
        actions.updateMessage(assistantMessageId, {
          content: accumulatedContent + ' [Cancelled]',
          isStreaming: false,
        });
        return null;
      }

      actions.setError(err.message);
      actions.updateMessage(assistantMessageId, {
        content: `Error: ${err.message}`,
        isError: true,
        isStreaming: false,
      });

      throw err;
    } finally {
      actions.setLoading(false);
      actions.setStreaming(false);
      abortControllerRef.current = null;
    }
  }, [state.conversationId, settings, actions]);

  /**
   * Cancel streaming query
   */
  const cancelStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
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
      actions.setConversation(data.id);
      actions.clearMessages();
      return data;
    } catch (err) {
      actions.setError(err.message);
      throw err;
    }
  }, [actions]);

  /**
   * Load an existing conversation
   */
  const loadConversation = useCallback(async (id) => {
    actions.setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/rag/conversations/${id}`, {
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error('Failed to load conversation');
      }

      const data = await response.json();
      actions.setConversation(data.id);

      // Convert messages to our format
      const formattedMessages = data.messages.map(msg => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        citations: msg.citations || [],
        confidenceScore: msg.confidence_score,
        timestamp: msg.created_at,
      }));

      actions.setMessages(formattedMessages);
      return data;
    } catch (err) {
      actions.setError(err.message);
      throw err;
    } finally {
      actions.setLoading(false);
    }
  }, [actions]);

  /**
   * List all conversations
   * Note: Empty dependency array - this is a pure fetch operation
   * that doesn't depend on any state. Error handling is done by caller.
   */
  const listConversations = useCallback(async (skip = 0, limit = 50) => {
    const response = await fetch(
      `${API_BASE}/rag/conversations?skip=${skip}&limit=${limit}`,
      { headers: getAuthHeaders() }
    );

    if (!response.ok) {
      throw new Error('Failed to list conversations');
    }

    return await response.json();
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
      if (id === state.conversationId) {
        actions.clearMessages();
      }

      return true;
    } catch (err) {
      actions.setError(err.message);
      throw err;
    }
  }, [state.conversationId, actions]);

  /**
   * Update a conversation's title
   */
  const updateConversation = useCallback(async (id, updates) => {
    try {
      const response = await fetch(`${API_BASE}/rag/conversations/${id}`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        throw new Error('Failed to update conversation');
      }

      return await response.json();
    } catch (err) {
      actions.setError(err.message);
      throw err;
    }
  }, [actions]);

  /**
   * Regenerate an assistant message
   * Replaces the message with a new response to the same query
   */
  const regenerateMessage = useCallback(async (query, messageIdToReplace, options = {}) => {
    actions.setLoading(true);
    actions.setError(null);

    // Update the message to show regenerating state
    actions.updateMessage(messageIdToReplace, {
      content: '',
      citations: [],
      isStreaming: true,
      isError: false,
    });

    try {
      if (settings.useStreaming) {
        // Create abort controller
        abortControllerRef.current = new AbortController();
        let accumulatedContent = '';

        const response = await fetch(`${API_BASE}/rag/query/stream`, {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify({
            query,
            conversation_id: state.conversationId,
            max_sources: options.maxSources ?? settings.maxSources,
            include_images: options.includeImages ?? settings.includeImages,
            include_graph: options.includeGraph ?? settings.includeGraph,
            min_similarity: options.minSimilarity ?? settings.minSimilarity,
          }),
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok) {
          throw new Error(`Request failed: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let citations = [];
        let usedIndices = [];
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
                    actions.updateMessage(messageIdToReplace, { content: accumulatedContent });
                    break;

                  case 'citations':
                    citations = data.citations;
                    usedIndices = data.used_indices;
                    break;

                  case 'metadata':
                    confidence = {
                      score: data.metadata.confidence_score,
                      level: data.metadata.confidence_level,
                    };
                    actions.setRetrievalMetadata(data.metadata);
                    break;

                  case 'error':
                    throw new Error(data.content);

                  case 'done':
                    actions.updateMessage(messageIdToReplace, {
                      content: accumulatedContent,
                      citations,
                      usedCitationIndices: usedIndices,
                      confidenceScore: confidence?.score,
                      confidenceLevel: confidence?.level,
                      isStreaming: false,
                      timestamp: new Date().toISOString(),
                    });
                    // Update active citations
                    if (citations && citations.length > 0) {
                      actions.setActiveCitations(citations);
                      const topCitation = citations[0];
                      actions.setPreview({
                        type: topCitation.source_type,
                        id: topCitation.source_id,
                        title: topCitation.title,
                        citation: topCitation,
                      });
                    }
                    break;
                }
              } catch (parseError) {
                console.warn('Failed to parse SSE data:', parseError);
              }
            }
          }
        }

        return { content: accumulatedContent, citations };
      } else {
        // Non-streaming regeneration
        const response = await fetch(`${API_BASE}/rag/query`, {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify({
            query,
            conversation_id: state.conversationId,
            max_sources: options.maxSources ?? settings.maxSources,
            include_images: options.includeImages ?? settings.includeImages,
            include_graph: options.includeGraph ?? settings.includeGraph,
            min_similarity: options.minSimilarity ?? settings.minSimilarity,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `Request failed: ${response.status}`);
        }

        const data = await response.json();

        // Update the message with new response
        actions.updateMessage(messageIdToReplace, {
          content: data.answer,
          citations: data.citations,
          usedCitationIndices: data.used_citation_indices,
          confidenceScore: data.confidence_score,
          confidenceLevel: data.confidence_level,
          isStreaming: false,
          timestamp: new Date().toISOString(),
        });

        actions.setRetrievalMetadata(data.retrieval_metadata);

        if (data.citations && data.citations.length > 0) {
          actions.setActiveCitations(data.citations);
          const topCitation = data.citations[0];
          actions.setPreview({
            type: topCitation.source_type,
            id: topCitation.source_id,
            title: topCitation.title,
            citation: topCitation,
          });
        }

        return data;
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        actions.updateMessage(messageIdToReplace, {
          content: '[Regeneration cancelled]',
          isStreaming: false,
        });
        return null;
      }

      actions.setError(err.message);
      actions.updateMessage(messageIdToReplace, {
        content: `Error: ${err.message}`,
        isError: true,
        isStreaming: false,
      });

      throw err;
    } finally {
      actions.setLoading(false);
      actions.setStreaming(false);
      abortControllerRef.current = null;
    }
  }, [state.conversationId, settings, actions]);

  return {
    // State (from context)
    messages: state.messages,
    isLoading: state.isLoading,
    isStreaming: state.isStreaming,
    error: state.error,
    conversationId: state.conversationId,
    lastRetrievalMetadata: state.lastRetrievalMetadata,
    previewItem: state.previewItem,

    // Query methods
    sendQuery,
    sendStreamingQuery,
    cancelStream,
    regenerateMessage,

    // Message management
    clearMessages: actions.clearMessages,

    // Conversation management
    startNewConversation,
    loadConversation,
    listConversations,
    deleteConversation,
    updateConversation,

    // Preview management
    setPreview: actions.setPreview,
    clearPreview: actions.clearPreview,
  };
}

export default useAIChat;
