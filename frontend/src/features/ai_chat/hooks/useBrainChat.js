/**
 * useBrainChat - Hook for Mnemosyne Brain chat API operations
 *
 * Handles brain-mode queries, streaming, and conversation management.
 * Used by useAIChat when chatMode === 'mnemosyne'.
 */

import { useCallback, useRef } from 'react';
import { useAIChatContext, useAIChatActions } from './AIChatContext';

const API_BASE = 'http://localhost:8000';

const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    'Authorization': token ? `Bearer ${token}` : '',
  };
};

export function useBrainChat() {
  const { state } = useAIChatContext();
  const actions = useAIChatActions();
  const abortControllerRef = useRef(null);

  /** Send a brain query (non-streaming) */
  const sendQuery = useCallback(async (query) => {
    actions.setLoading(true);
    actions.setError(null);

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: query,
      timestamp: new Date().toISOString(),
    };
    actions.addMessage(userMessage);

    try {
      const response = await fetch(`${API_BASE}/mnemosyne/query`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          query,
          conversation_id: state.conversationId,
          auto_create_conversation: true,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Request failed: ${response.status}`);
      }

      const data = await response.json();

      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.answer,
        brainFilesUsed: data.brain_files_used,
        topicsMatched: data.topics_matched,
        isBrainMode: true,
        timestamp: new Date().toISOString(),
      };
      actions.addMessage(assistantMessage);

      if (data.conversation_id && data.conversation_id !== state.conversationId) {
        actions.setConversation(data.conversation_id);
      }
      actions.setBrainFilesUsed(data.brain_files_used || []);
      actions.setTopicsMatched(data.topics_matched || []);

      return data;
    } catch (err) {
      actions.setError(err.message);
      actions.addMessage({
        id: Date.now() + 1,
        role: 'assistant',
        content: `Error: ${err.message}`,
        isError: true,
        timestamp: new Date().toISOString(),
      });
      throw err;
    } finally {
      actions.setLoading(false);
    }
  }, [state.conversationId, actions]);

  /** Send a streaming brain query (SSE) */
  const sendStreamingQuery = useCallback(async (query) => {
    actions.setLoading(true);
    actions.setStreaming(true);
    actions.setError(null);

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: query,
      timestamp: new Date().toISOString(),
    };
    actions.addMessage(userMessage);

    const assistantMessageId = Date.now() + 1;
    actions.addMessage({
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      isBrainMode: true,
      isStreaming: true,
      timestamp: new Date().toISOString(),
    });

    abortControllerRef.current = new AbortController();
    let accumulatedContent = '';

    try {
      const response = await fetch(`${API_BASE}/mnemosyne/query/stream`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          query,
          conversation_id: state.conversationId,
          auto_create_conversation: true,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let brainMeta = {};

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(line.slice(6));

            switch (data.type) {
              case 'token':
                accumulatedContent += data.content;
                actions.updateMessage(assistantMessageId, { content: accumulatedContent });
                break;

              case 'brain_meta':
                brainMeta = {
                  brainFilesUsed: data.brain_files_used || [],
                  topicsMatched: data.topics_matched || [],
                };
                actions.setBrainFilesUsed(brainMeta.brainFilesUsed);
                actions.setTopicsMatched(brainMeta.topicsMatched);
                break;

              case 'metadata':
                if (data.metadata?.conversation_id &&
                    data.metadata.conversation_id !== state.conversationId) {
                  actions.setConversation(data.metadata.conversation_id);
                }
                break;

              case 'error':
                throw new Error(data.content);

              case 'done':
                actions.updateMessage(assistantMessageId, {
                  content: accumulatedContent,
                  brainFilesUsed: brainMeta.brainFilesUsed,
                  topicsMatched: brainMeta.topicsMatched,
                  isBrainMode: true,
                  isStreaming: false,
                });
                break;
            }
          } catch (parseError) {
            if (parseError.message?.startsWith('Request failed')) throw parseError;
          }
        }
      }

      return { content: accumulatedContent };
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
  }, [state.conversationId, actions]);

  const cancelStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  const listConversations = useCallback(async (skip = 0, limit = 50) => {
    const response = await fetch(
      `${API_BASE}/mnemosyne/conversations?skip=${skip}&limit=${limit}`,
      { headers: getAuthHeaders() }
    );
    if (!response.ok) throw new Error('Failed to list brain conversations');
    return await response.json();
  }, []);

  const loadConversation = useCallback(async (id) => {
    actions.setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/mnemosyne/conversations/${id}`, {
        headers: getAuthHeaders(),
      });
      if (!response.ok) throw new Error('Failed to load brain conversation');

      const data = await response.json();
      actions.setConversation(data.id);

      const formattedMessages = (data.messages || []).map(msg => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        brainFilesUsed: msg.brain_files_loaded,
        topicsMatched: msg.topics_matched,
        isBrainMode: true,
        timestamp: msg.created_at,
      }));

      actions.setMessages(formattedMessages);
      if (data.brain_files_used) {
        actions.setBrainFilesUsed(data.brain_files_used);
      }
      return data;
    } catch (err) {
      actions.setError(err.message);
      throw err;
    } finally {
      actions.setLoading(false);
    }
  }, [actions]);

  const deleteConversation = useCallback(async (id) => {
    const response = await fetch(`${API_BASE}/mnemosyne/conversations/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!response.ok) throw new Error('Failed to delete brain conversation');
    if (id === state.conversationId) {
      actions.clearMessages();
    }
    return true;
  }, [state.conversationId, actions]);

  const updateConversation = useCallback(async (id, updates) => {
    const response = await fetch(`${API_BASE}/mnemosyne/conversations/${id}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(updates),
    });
    if (!response.ok) throw new Error('Failed to update brain conversation');
    return await response.json();
  }, []);

  return {
    sendQuery,
    sendStreamingQuery,
    cancelStream,
    listConversations,
    loadConversation,
    deleteConversation,
    updateConversation,
  };
}

export default useBrainChat;
