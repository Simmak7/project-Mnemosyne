import React, { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useWorkspaceState } from '../../hooks/useWorkspaceState';
import { useContentAnalysis } from '../../hooks/useContentAnalysis';
import { Info, Calendar, FileText, Hash, Link2, Image as ImageIcon, Activity } from 'lucide-react';
import { format } from 'date-fns';
import './ContextPanels.css';

/**
 * InfoPanel - Displays note metadata and statistics (Phase 4 - Real-time updates)
 * Shows live stats when editor is active, fetched stats in read-only mode
 */
function InfoPanel() {
  const { selectedNoteId, editorState } = useWorkspaceState();

  // Fetch note data using React Query
  const { data: note, isLoading: loading, error } = useQuery({
    queryKey: ['note', selectedNoteId],
    queryFn: async () => {
      if (!selectedNoteId) return null;

      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token');
      }

      const response = await fetch(`http://localhost:8000/notes/${selectedNoteId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch note');
      }

      return response.json();
    },
    enabled: !!selectedNoteId,
    staleTime: 30000, // Consider data fresh for 30 seconds
    refetchOnWindowFocus: false,
  });

  // Real-time content analysis when in edit mode
  const editorAnalysis = useContentAnalysis(editorState.editorInstance, editorState.noteTitle);

  // Use live stats from editor if in edit mode, otherwise use fetched note data
  const stats = useMemo(() => {
    if (editorState.isEditMode && editorState.editorInstance) {
      return {
        wordCount: editorAnalysis.wordCount,
        charCount: editorAnalysis.charCount,
        wikilinks: editorAnalysis.wikilinks,
        hashtags: editorAnalysis.hashtags,
        isLive: true,
      };
    }

    if (note) {
      const plainText = note.content || '';
      const wordCount = plainText.trim().split(/\s+/).filter(w => w.length > 0).length;
      const charCount = plainText.length;

      return {
        wordCount,
        charCount,
        wikilinks: note.wikilinks || [],
        hashtags: note.tags || [],
        isLive: false,
      };
    }

    return {
      wordCount: 0,
      charCount: 0,
      wikilinks: [],
      hashtags: [],
      isLive: false,
    };
  }, [editorState.isEditMode, editorState.editorInstance, editorAnalysis, note]);

  if (!selectedNoteId) {
    return (
      <div className="info-panel">
        <div className="panel-empty">
          <Info size={40} className="empty-icon" />
          <p>Select a note to see info</p>
        </div>
      </div>
    );
  }

  if (loading && !editorState.isEditMode) {
    return (
      <div className="info-panel">
        <div className="panel-loading">
          <div className="loading-spinner"></div>
          <p>Loading info...</p>
        </div>
      </div>
    );
  }

  if (error && !editorState.isEditMode) {
    return (
      <div className="info-panel">
        <div className="panel-empty">
          <Info size={40} className="empty-icon" />
          <p>Error loading info</p>
          <span className="empty-subtitle">{error.message}</span>
        </div>
      </div>
    );
  }

  if (!note && !editorState.isEditMode) {
    return (
      <div className="info-panel">
        <div className="panel-empty">
          <Info size={40} className="empty-icon" />
          <p>Note not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="info-panel">
      {/* Live indicator */}
      {stats.isLive && (
        <div className="info-live-indicator">
          <Activity size={14} className="live-icon pulsing" />
          <span>Live stats</span>
        </div>
      )}

      {/* Dates section - only show if note is loaded */}
      {note && (
        <div className="info-section">
          <h4 className="info-section-title">
            <Calendar size={16} />
            Dates
          </h4>
          <div className="info-item">
            <span className="info-label">Created</span>
            <span className="info-value">
              {format(new Date(note.created_at), 'PPP p')}
            </span>
          </div>
          {note.updated_at && note.updated_at !== note.created_at && (
            <div className="info-item">
              <span className="info-label">Updated</span>
              <span className="info-value">
                {format(new Date(note.updated_at), 'PPP p')}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Content stats - real-time in edit mode */}
      <div className="info-section">
        <h4 className="info-section-title">
          <FileText size={16} />
          Content {stats.isLive && <span className="live-badge">Live</span>}
        </h4>
        <div className="info-item">
          <span className="info-label">Words</span>
          <span className={`info-value ${stats.isLive ? 'live-value' : ''}`}>
            {stats.wordCount.toLocaleString()}
          </span>
        </div>
        <div className="info-item">
          <span className="info-label">Characters</span>
          <span className={`info-value ${stats.isLive ? 'live-value' : ''}`}>
            {stats.charCount.toLocaleString()}
          </span>
        </div>
      </div>

      {/* Connections - real-time in edit mode */}
      <div className="info-section">
        <h4 className="info-section-title">
          <Hash size={16} />
          Connections {stats.isLive && <span className="live-badge">Live</span>}
        </h4>
        <div className="info-item">
          <span className="info-label">Tags</span>
          <span className={`info-value ${stats.isLive ? 'live-value' : ''}`}>
            {stats.hashtags.length}
          </span>
        </div>
        <div className="info-item">
          <span className="info-label">Wikilinks</span>
          <span className={`info-value ${stats.isLive ? 'live-value' : ''}`}>
            {stats.wikilinks.length}
          </span>
        </div>
        {note && note.image_id && (
          <div className="info-item">
            <span className="info-label">
              <ImageIcon size={14} />
              Linked Image
            </span>
            <span className="info-value">Yes</span>
          </div>
        )}
      </div>

      {/* Tags details */}
      {stats.hashtags && stats.hashtags.length > 0 && (
        <div className="info-section">
          <h4 className="info-section-title">
            <Hash size={16} />
            Tags {stats.isLive && <span className="live-badge">Live</span>}
          </h4>
          <div className="info-tags">
            {stats.hashtags.map((tag, index) => (
              <span key={index} className={`info-tag ${stats.isLive ? 'live-tag' : ''}`}>
                #{typeof tag === 'string' ? tag : tag.name || tag}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Wikilinks details */}
      {stats.wikilinks && stats.wikilinks.length > 0 && (
        <div className="info-section">
          <h4 className="info-section-title">
            <Link2 size={16} />
            Linked Notes {stats.isLive && <span className="live-badge">Live</span>}
          </h4>
          <div className="info-wikilinks">
            {stats.wikilinks.map((link, index) => (
              <div key={index} className={`info-wikilink ${stats.isLive ? 'live-wikilink' : ''}`}>
                [[{link}]]
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default InfoPanel;
