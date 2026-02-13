/**
 * Conversation API methods
 */
import { api } from '../../../../utils/api';

/**
 * Start a new conversation
 */
export async function createConversation(title = null) {
  return await api.post('/rag/conversations', { title });
}

/**
 * Load an existing conversation
 */
export async function fetchConversation(id) {
  const data = await api.get(`/rag/conversations/${id}`);

  // Convert messages to our format
  const formattedMessages = data.messages.map(msg => ({
    id: msg.id,
    role: msg.role,
    content: msg.content,
    citations: msg.citations || [],
    confidenceScore: msg.confidence_score,
    timestamp: msg.created_at,
    isNexusMode: msg.citations?.some(c => c.origin_type != null || c.community_id != null) || false,
  }));

  return {
    ...data,
    messages: formattedMessages,
    connectionInsights: data.connection_insights || [],
    explorationSuggestions: data.exploration_suggestions || [],
  };
}

/**
 * List all conversations
 */
export async function listConversations(skip = 0, limit = 50) {
  return await api.get(`/rag/conversations?skip=${skip}&limit=${limit}`);
}

/**
 * Delete a conversation
 */
export async function deleteConversation(id) {
  await api.delete(`/rag/conversations/${id}`);
  return true;
}

/**
 * Update a conversation's title
 */
export async function updateConversation(id, updates) {
  return await api.put(`/rag/conversations/${id}`, updates);
}
