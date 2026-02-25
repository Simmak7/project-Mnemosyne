/**
 * DiscoveryPanel - Orphaned and Hub notes discovery
 *
 * Shows quick-jump lists for disconnected notes (orphans)
 * and most-connected notes (hubs) when no node is focused.
 */

import React from 'react';
import { Unlink, Star, FileText, Loader2 } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { API_URL as API_BASE } from '../../../utils/api';

async function apiFetch(path, signal) {
  const token = localStorage.getItem('token');
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
    signal,
  });
  if (!res.ok) return [];
  return res.json();
}

export function DiscoveryPanel({ onFocusNode }) {
  const { data: orphans, isLoading: orphansLoading } = useQuery({
    queryKey: ['graph', 'orphaned'],
    queryFn: ({ signal }) => apiFetch('/notes/orphaned/list', signal),
    staleTime: 120_000,
    gcTime: 10 * 60_000,
  });

  const { data: hubs, isLoading: hubsLoading } = useQuery({
    queryKey: ['graph', 'most-linked'],
    queryFn: ({ signal }) => apiFetch('/notes/most-linked/?limit=5', signal),
    staleTime: 120_000,
    gcTime: 10 * 60_000,
  });

  const orphanList = Array.isArray(orphans) ? orphans.slice(0, 5) : [];
  const hubList = Array.isArray(hubs) ? hubs.slice(0, 5) : [];

  const handleClick = (item) => {
    const noteId = item.id || item.note_id;
    if (noteId) onFocusNode?.(`note-${noteId}`);
  };

  return (
    <div className="discovery-panel">
      {/* Hub Notes */}
      <div className="discovery-panel__section">
        <div className="discovery-panel__header">
          <Star size={14} />
          <span>Hub Notes</span>
          <span className="discovery-panel__badge">Most connected</span>
        </div>

        {hubsLoading && (
          <div className="discovery-panel__loading">
            <Loader2 size={14} className="is-spinning" />
          </div>
        )}

        {!hubsLoading && hubList.length === 0 && (
          <p className="discovery-panel__empty">No hub notes yet</p>
        )}

        {!hubsLoading && hubList.map((item) => (
          <button
            key={item.id || item.note_id}
            className="discovery-panel__item"
            onClick={() => handleClick(item)}
          >
            <FileText size={12} />
            <span className="discovery-panel__item-title">
              {item.title || `Note ${item.id}`}
            </span>
            {(item.backlink_count || item.count) > 0 && (
              <span className="discovery-panel__item-count">
                {item.backlink_count || item.count} links
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Orphaned Notes */}
      <div className="discovery-panel__section">
        <div className="discovery-panel__header">
          <Unlink size={14} />
          <span>Disconnected</span>
          <span className="discovery-panel__badge">No connections</span>
        </div>

        {orphansLoading && (
          <div className="discovery-panel__loading">
            <Loader2 size={14} className="is-spinning" />
          </div>
        )}

        {!orphansLoading && orphanList.length === 0 && (
          <p className="discovery-panel__empty">All notes are connected</p>
        )}

        {!orphansLoading && orphanList.map((item) => (
          <button
            key={item.id || item.note_id}
            className="discovery-panel__item discovery-panel__item--orphan"
            onClick={() => handleClick(item)}
          >
            <FileText size={12} />
            <span className="discovery-panel__item-title">
              {item.title || `Note ${item.id}`}
            </span>
          </button>
        ))}

        {!orphansLoading && orphanList.length > 0 && orphans?.length > 5 && (
          <p className="discovery-panel__more">
            +{orphans.length - 5} more disconnected notes
          </p>
        )}
      </div>
    </div>
  );
}

export default DiscoveryPanel;
