/**
 * BacklinksSection - Shows notes that link TO the selected node
 *
 * Fetches backlinks from the legacy /notes/{id}/backlinks endpoint
 * and displays them as clickable items in the Inspector.
 */

import React from 'react';
import { ArrowLeft, FileText, Loader2 } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

async function fetchBacklinks(noteId, signal) {
  const token = localStorage.getItem('token');
  const res = await fetch(`${API_BASE}/notes/${noteId}/backlinks`, {
    headers: { Authorization: `Bearer ${token}` },
    signal,
  });
  if (!res.ok) return [];
  return res.json();
}

export function BacklinksSection({ nodeId, onFocusNode }) {
  // Extract numeric ID from "note-123" format
  const [type, ...idParts] = (nodeId || '').split('-');
  const numericId = idParts.join('-');

  const { data: backlinks, isLoading } = useQuery({
    queryKey: ['graph', 'backlinks', numericId],
    queryFn: ({ signal }) => fetchBacklinks(numericId, signal),
    enabled: type === 'note' && !!numericId,
    staleTime: 60_000,
    gcTime: 5 * 60_000,
  });

  // Only show for note nodes
  if (type !== 'note' || !numericId) return null;

  return (
    <section className="inspector__section">
      <h4 className="inspector__section-title">
        <ArrowLeft size={14} />
        Backlinks
      </h4>

      {isLoading && (
        <div className="inspector__backlinks-loading">
          <Loader2 size={14} className="is-spinning" />
        </div>
      )}

      {!isLoading && (!backlinks || backlinks.length === 0) && (
        <p className="inspector__empty-connections">No backlinks found</p>
      )}

      {!isLoading && backlinks?.length > 0 && (
        <div className="inspector__backlinks-list">
          {backlinks.map((bl) => (
            <button
              key={bl.id || bl.note_id}
              className="inspector__backlink-item"
              onClick={() => onFocusNode?.(`note-${bl.id || bl.note_id}`)}
              title={`Focus on "${bl.title}"`}
            >
              <FileText size={12} />
              <span className="inspector__backlink-title">
                {bl.title || `Note ${bl.id || bl.note_id}`}
              </span>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}

export default BacklinksSection;
