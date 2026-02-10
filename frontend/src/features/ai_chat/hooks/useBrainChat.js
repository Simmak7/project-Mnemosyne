/**
 * useBrainChat - Hook for Mnemosyne Brain chat API operations
 *
 * Handles brain-mode queries, streaming, and conversation management.
 * Used by useAIChat when chatMode === 'mnemosyne'.
 */

import { useCallback, useRef } from 'react';
import { useAIChatContext, useAIChatActions } from './AIChatContext';
import { api } from '../../../utils/api';

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
      const data = await api.post('/mnemosyne/query', {
        query,
        conversation_id: state.conversationId,
        auto_create_conversation: true,
      });

      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.answer,
        brainFilesUsed: data.brain_files_used,
        topicsMatched: data.topics_matched,
        modelUsed: data.model_used,
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
      // Use api.fetch for streaming requests with proper CSRF handling
      const response = await api.fetch('/mnemosyne/query/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          conversation_id: state.conversationId,
          auto_create_conversation: true,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Request failed: ${response.status}`);
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
                  modelUsed: data.model_used,
                };
                actions.setBrainFilesUsed(brainMeta.brainFilesUsed);
                actions.setTopicsMatched(brainMeta.topicsMatched);
                break;

              case 'metadata':
                if (data.metadata?.conversation_id &&
                    data.metadata.conversation_id !== state.conversationId) {
                  actions.setConversation(data.metadata.conversation_id);
                }
                // Also capture model_used from metadata
                if (data.metadata?.model_used) {
                  brainMeta.modelUsed = data.metadata.model_used;
                }
                break;

              case 'error':
                throw new Error(data.content);

              case 'done':
                actions.updateMessage(assistantMessageId, {
                  content: accumulatedContent,
                  brainFilesUsed: brainMeta.brainFilesUsed,
                  topicsMatched: brainMeta.topicsMatched,
                  modelUsed: brainMeta.modelUsed,
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
    return await api.get(`/mnemosyne/conversations?skip=${skip}&limit=${limit}`);
  }, []);

  const loadConversation = useCallback(async (id) => {
    actions.setLoading(true);
    try {
      const data = await api.get(`/mnemosyne/conversations/${id}`);
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
    await api.delete(`/mnemosyne/conversations/${id}`);
    if (id === state.conversationId) {
      actions.clearMessages();
    }
    return true;
  }, [state.conversationId, actions]);

  const updateConversation = useCallback(async (id, updates) => {
    return await api.put(`/mnemosyne/conversations/${id}`, updates);
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
