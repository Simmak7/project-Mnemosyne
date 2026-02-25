/**
 * useDashboardData - Parallel data fetching for dashboard widgets
 *
 * Uses React Query + Promise.allSettled so individual widget
 * failures don't break the entire dashboard.
 */
import { useQuery } from '@tanstack/react-query';
import { api } from '../../../utils/api';

function settled(promise) {
  return promise.then(
    (value) => ({ status: 'fulfilled', value }),
    () => ({ status: 'rejected', value: null })
  );
}

async function fetchDashboardData() {
  const [
    health, gpuInfo, graphStats, recentNotes, imageRes,
    tags, mostLinked, embeddings, brainStatus, ragConversations,
    documents, favImages,
  ] = await Promise.all([
    settled(api.get('/health')),
    settled(api.get('/system/gpu-info')),
    settled(api.get('/graph/stats')),
    settled(api.get('/buckets/inbox')),
    settled(api.get('/images/?limit=1')),
    settled(api.get('/tags/')),
    settled(api.get('/notes/most-linked/?limit=5')),
    settled(api.get('/search/embeddings/coverage')),
    settled(api.get('/brain/status')),
    settled(api.get('/rag/conversations?limit=1')),
    settled(api.get('/documents/?limit=1')),
    settled(api.get('/images/favorites/?limit=8')),
  ]);

  return {
    health: health.value,
    gpuInfo: gpuInfo.value,
    graphStats: graphStats.value,
    recentNotes: recentNotes.value,
    images: imageRes.value,
    tags: tags.value,
    mostLinked: mostLinked.value,
    embeddings: embeddings.value,
    brainStatus: brainStatus.value,
    ragConversations: ragConversations.value,
    documents: documents.value,
    favoriteImages: favImages.value,
  };
}

export function useDashboardData() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: fetchDashboardData,
    staleTime: 60_000,
    gcTime: 5 * 60_000,
    refetchOnWindowFocus: true,
  });

  return { data: data || {}, isLoading, error, refetch };
}

export default useDashboardData;
