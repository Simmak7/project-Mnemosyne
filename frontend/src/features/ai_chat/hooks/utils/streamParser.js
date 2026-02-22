/**
 * Stream parsing utilities for RAG chat
 */

/**
 * Parse SSE stream events and dispatch to handlers
 */
export async function parseSSEStream(reader, handlers) {
  const decoder = new TextDecoder();
  let accumulatedContent = '';
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
              handlers.onToken?.(accumulatedContent);
              break;

            case 'citations':
              citations = data.citations;
              usedIndices = data.used_indices;
              break;

            case 'metadata':
              confidence = {
                score: data.metadata.confidence_score,
                level: data.metadata.confidence_level,
                modelUsed: data.metadata.model_used,
              };
              handlers.onMetadata?.(data.metadata, confidence);
              break;

            case 'error':
              throw new Error(data.content);

            case 'done':
              handlers.onDone?.({
                content: accumulatedContent,
                citations,
                usedIndices,
                confidence,
              });
              break;
          }
        } catch (parseError) {
          if (parseError.message && !parseError.message.includes('parse')) {
            throw parseError;
          }
          console.warn('Failed to parse SSE data:', parseError);
        }
      }
    }
  }

  return { content: accumulatedContent, citations, usedIndices, confidence };
}

/**
 * Create a user message object
 */
export function createUserMessage(content) {
  return {
    id: Date.now(),
    role: 'user',
    content,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Create an assistant message placeholder for streaming
 */
export function createAssistantPlaceholder() {
  return {
    id: Date.now() + 1,
    role: 'assistant',
    content: '',
    citations: [],
    usedCitationIndices: [],
    isStreaming: true,
    timestamp: new Date().toISOString(),
  };
}
