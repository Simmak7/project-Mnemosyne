import React, { useMemo } from 'react';
import {
  Calendar,
  FileText,
  Hash,
  Link2,
  ArrowDownLeft,
  Image,
  Type
} from 'lucide-react';

/**
 * NoteInfoTab - Shows note metadata and statistics
 */
function NoteInfoTab({ note }) {
  // Calculate statistics
  const stats = useMemo(() => {
    const content = note.content || '';
    const words = content.trim().split(/\s+/).filter(w => w.length > 0).length;
    const characters = content.length;
    const paragraphs = content.split(/\n\n+/).filter(p => p.trim()).length;
    const lines = content.split('\n').length;

    return { words, characters, paragraphs, lines };
  }, [note.content]);

  // Format date helper
  const formatDate = (dateStr) => {
    if (!dateStr) return 'Unknown';
    const date = new Date(dateStr);
    return date.toLocaleString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  // Format relative time
  const formatRelative = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins} minutes ago`;
    if (diffHours < 24) return `${diffHours} hours ago`;
    if (diffDays < 7) return `${diffDays} days ago`;
    return '';
  };

  return (
    <div className="note-info-tab">
      {/* Dates section */}
      <section className="info-section">
        <h4 className="section-header">
          <Calendar size={14} />
          Dates
        </h4>
        <div className="info-grid">
          <div className="info-item">
            <span className="info-label">Created</span>
            <span className="info-value">{formatDate(note.created_at)}</span>
            {formatRelative(note.created_at) && (
              <span className="info-relative">{formatRelative(note.created_at)}</span>
            )}
          </div>
          {note.updated_at && note.updated_at !== note.created_at && (
            <div className="info-item">
              <span className="info-label">Last Modified</span>
              <span className="info-value">{formatDate(note.updated_at)}</span>
              {formatRelative(note.updated_at) && (
                <span className="info-relative">{formatRelative(note.updated_at)}</span>
              )}
            </div>
          )}
        </div>
      </section>

      {/* Statistics section */}
      <section className="info-section">
        <h4 className="section-header">
          <Type size={14} />
          Statistics
        </h4>
        <div className="stats-grid">
          <div className="stat-item">
            <span className="stat-value">{stats.words}</span>
            <span className="stat-label">Words</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{stats.characters}</span>
            <span className="stat-label">Characters</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{stats.paragraphs}</span>
            <span className="stat-label">Paragraphs</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{stats.lines}</span>
            <span className="stat-label">Lines</span>
          </div>
        </div>
      </section>

      {/* Connections section */}
      <section className="info-section">
        <h4 className="section-header">
          <Link2 size={14} />
          Connections
        </h4>
        <div className="info-grid">
          <div className="info-item">
            <span className="info-label">
              <Link2 size={12} />
              Outgoing Links
            </span>
            <span className="info-value">{note.linked_notes?.length || 0}</span>
          </div>
          <div className="info-item">
            <span className="info-label">
              <ArrowDownLeft size={12} />
              Backlinks
            </span>
            <span className="info-value">{note.backlinks?.length || 0}</span>
          </div>
          <div className="info-item">
            <span className="info-label">
              <Hash size={12} />
              Tags
            </span>
            <span className="info-value">{note.tags?.length || 0}</span>
          </div>
          <div className="info-item">
            <span className="info-label">
              <Image size={12} />
              Images
            </span>
            <span className="info-value">{note.image_ids?.length || 0}</span>
          </div>
        </div>
      </section>

      {/* Technical info */}
      <section className="info-section">
        <h4 className="section-header">
          <FileText size={14} />
          Technical
        </h4>
        <div className="info-grid">
          <div className="info-item">
            <span className="info-label">Note ID</span>
            <span className="info-value mono">{note.id}</span>
          </div>
          {note.slug && (
            <div className="info-item">
              <span className="info-label">Slug</span>
              <span className="info-value mono">{note.slug}</span>
            </div>
          )}
          <div className="info-item">
            <span className="info-label">Type</span>
            <span className="info-value">
              {note.is_standalone === false ? 'AI Generated' : 'Manual'}
            </span>
          </div>
        </div>
      </section>
    </div>
  );
}

export default NoteInfoTab;
