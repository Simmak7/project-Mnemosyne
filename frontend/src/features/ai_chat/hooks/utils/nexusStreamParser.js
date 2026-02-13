/**
 * NEXUS Stream parsing utilities
 *
 * Handles additional NEXUS-specific events: connections, suggestions
 */

export async function parseNexusSSEStream(reader, handlers) {
  const decoder = new TextDecoder();
  let accumulatedContent = '';
  let citations = [];
  let usedIndices = [];
  let connections = [];
  let suggestions = [];
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
              citations = data.citations || [];
              usedIndices = data.used_indices || [];
              handlers.onCitations?.(citations, usedIndices);
              break;

            case 'connections':
              connections = data.connections || [];
              handlers.onConnections?.(connections);
              break;

            case 'suggestions':
              suggestions = data.suggestions || [];
              handlers.onSuggestions?.(suggestions);
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
                connections,
                suggestions,
                confidence,
              });
              break;
          }
        } catch (parseError) {
          if (parseError.message && !parseError.message.includes('parse')) {
            throw parseError;
          }
          console.warn('Failed to parse NEXUS SSE data:', parseError);
        }
      }
    }
  }

  return { content: accumulatedContent, citations, usedIndices, connections, suggestions, confidence };
}
