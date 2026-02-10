/**
 * useDocuments Hook
 * React Query hooks for document CRUD operations.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../../utils/api';

const QUERY_KEY = 'documents';

/**
 * Fetch documents list with optional status filter and sorting
 */
export function useDocuments(statusFilter = null, sortBy = null, sortOrder = null, collectionId = null) {
  return useQuery({
    queryKey: [QUERY_KEY, statusFilter, sortBy, sortOrder, collectionId],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (statusFilter) params.set('status', statusFilter);
      if (sortBy) params.set('sort_by', sortBy);
      if (sortOrder) params.set('sort_order', sortOrder);
      if (collectionId) params.set('collection_id', collectionId);
      params.set('limit', '100');
      return api.get(`/documents/?${params.toString()}`);
    },
    staleTime: 15000,
    // Poll every 5s when any document is queued/processing
    refetchInterval: (query) => {
      const docs = query.state.data?.documents;
      if (!docs) return false;
      const hasActive = docs.some(d =>
        d.ai_analysis_status === 'queued' || d.ai_analysis_status === 'processing'
      );
      return hasActive ? 5000 : false;
    },
  });
}

/**
 * Fetch single document detail
 */
export function useDocument(docId) {
  return useQuery({
    queryKey: [QUERY_KEY, docId],
    queryFn: () => api.get(`/documents/${docId}`),
    enabled: !!docId,
  });
}

/**
 * Approve document and create summary note
 */
export function useApproveDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ docId, data }) => api.post(`/documents/${docId}/approve`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QUERY_KEY] });
      qc.invalidateQueries({ queryKey: ['notes-enhanced'] });
    },
  });
}

/**
 * Reject/skip review
 */
export function useRejectDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (docId) => api.post(`/documents/${docId}/reject`),
    onSuccess: () => qc.invalidateQueries({ queryKey: [QUERY_KEY] }),
  });
}

/**
 * Delete (trash) document
 */
export function useDeleteDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (docId) => api.delete(`/documents/${docId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: [QUERY_KEY] }),
  });
}

/**
 * Retry failed analysis
 */
export function useRetryDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (docId) => api.post(`/documents/${docId}/retry`),
    onSuccess: () => qc.invalidateQueries({ queryKey: [QUERY_KEY] }),
  });
}

/**
 * Extract full text and append to summary note
 */
export function useExtractToNote() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (docId) => api.post(`/documents/${docId}/extract-to-note`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [QUERY_KEY] });
      qc.invalidateQueries({ queryKey: ['notes-enhanced'] });
    },
  });
}

/**
 * Update suggestions before approval
 */
export function useUpdateSuggestions() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ docId, data }) => api.put(`/documents/${docId}/suggestions`, data),
    onSuccess: (_, { docId }) =>
      qc.invalidateQueries({ queryKey: [QUERY_KEY, docId] }),
  });
}
