/**
 * useBrainFocus - Reads Brain graph focus node from localStorage
 * and fetches its data from the appropriate endpoint.
 */
import { useQuery } from '@tanstack/react-query';
import { usePersistedState } from '../../../hooks/usePersistedState';
import { api } from '../../../utils/api';

function parseNodeId(compositeId) {
  if (!compositeId) return { type: null, id: null };
  const match = compositeId.match(/^(note|tag|image|entity)-(.+)$/);
  if (!match) return { type: null, id: null };
  return { type: match[1], id: match[2] };
}

function fetchNodeData(type, id) {
  if (type === 'note') return api.get(`/notes/${id}/enhanced`);
  if (type === 'image') return api.get(`/images/${id}`);
  return Promise.resolve(null);
}

export function useBrainFocus() {
  const [focusNodeId] = usePersistedState('brain:focusNodeId', null);
  const { type: nodeType, id: nodeId } = parseNodeId(focusNodeId);

  const { data: node, isLoading } = useQuery({
    queryKey: ['brain-focus', nodeType, nodeId],
    queryFn: () => fetchNodeData(nodeType, nodeId),
    enabled: !!nodeType && !!nodeId && (nodeType === 'note' || nodeType === 'image'),
    staleTime: 30_000,
    gcTime: 2 * 60_000,
  });

  return { node, isLoading, nodeType, nodeId, focusNodeId };
}

export default useBrainFocus;
