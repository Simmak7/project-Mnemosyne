/**
 * useGraphRebuild - Hooks for graph rebuild operations and AI stats
 *
 * Wraps the backend /graph/semantic/*, /graph/communities/*, /graph/index/* endpoints.
 * Uses React Query mutations for POST calls, queries for stats.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../../utils/api';

/** POST with query params via the api utility (handles CSRF + auth) */
async function graphPost(path, params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => query.set(k, String(v)));
  const fullPath = query.toString() ? `${path}?${query}` : path;
  return api.post(fullPath);
}

/** GET via the api utility (handles auth) */
async function graphGet(path, signal) {
  return api.get(path, { signal });
}

/** Fetch semantic edge statistics */
export function useSemanticStats() {
  const query = useQuery({
    queryKey: ['graph', 'semantic', 'stats'],
    queryFn: ({ signal }) => graphGet('/graph/semantic/stats', signal),
    staleTime: 60_000,
    gcTime: 5 * 60_000,
  });
  return { data: query.data ?? null, isLoading: query.isLoading, refetch: query.refetch };
}

/** Fetch community statistics */
export function useCommunityStats() {
  const query = useQuery({
    queryKey: ['graph', 'communities', 'stats'],
    queryFn: ({ signal }) => graphGet('/graph/communities/stats', signal),
    staleTime: 60_000,
    gcTime: 5 * 60_000,
  });
  return { data: query.data ?? null, isLoading: query.isLoading, refetch: query.refetch };
}

/** Combined hook for all rebuild operations */
export function useGraphRebuild() {
  const queryClient = useQueryClient();

  const invalidateAll = () => {
    queryClient.invalidateQueries({ queryKey: ['graph'] });
  };

  const semanticRebuild = useMutation({
    mutationFn: ({ threshold = 0.85 } = {}) =>
      graphPost('/graph/semantic/rebuild', { threshold, use_celery: true }),
    onSuccess: invalidateAll,
  });

  const clearSemantic = useMutation({
    mutationFn: () => api.delete('/graph/semantic/clear'),
    onSuccess: invalidateAll,
  });

  const communityRebuild = useMutation({
    mutationFn: ({ algorithm = 'louvain' } = {}) =>
      graphPost('/graph/communities/rebuild', { algorithm, use_celery: true }),
    onSuccess: invalidateAll,
  });

  const fullRebuild = useMutation({
    mutationFn: ({ includeSemantic = true, includeClustering = true } = {}) =>
      graphPost('/graph/index/rebuild', {
        include_semantic: includeSemantic,
        include_clustering: includeClustering,
      }),
    onSuccess: invalidateAll,
  });

  return { semanticRebuild, clearSemantic, communityRebuild, fullRebuild, invalidateAll };
}
