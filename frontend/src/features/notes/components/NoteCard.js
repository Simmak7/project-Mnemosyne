import React, { useMemo } from 'react';
import { Sparkles, FileText, Calendar, Image, Hash, Clock, ExternalLink, Camera } from 'lucide-react';
import './NoteCard.css';

/**
 * NoteCard - Individual note card component
 * Displays note preview with thumbnail, title, excerpt, and tags
 */
function NoteCard({
  note,
  isSelected,
  onClick,
  onDoubleClick,
  searchQuery
}) {
  // Determine note type for badge using source field
  const noteType = useMemo(() => {
    const isDaily = note.title?.startsWith('Daily Note') ||
                    note.title?.match(/^\d{4}-\d{2}-\d{2}/) ||
                    note.title?.toLowerCase().includes('journal');

    if (isDaily) return 'daily';
    if (note.source === 'document_analysis') return 'doc_ai';
    if (note.source === 'image_analysis') return 'photo_ai';
    // Fallback for old notes without source field
    const hasImages = note.image_ids && note.image_ids.length > 0;
    if (hasImages || note.is_standalone === false) return 'photo_ai';
    return 'manual';
  }, [note]);

  // Extract first ~100 chars of content as preview
  const excerpt = useMemo(() => {
    if (!note.content) return '';
    const plainText = note.content
      .replace(/#{1,6}\s/g, '')
      .replace(/\*\*|__/g, '')
      .replace(/\*|_/g, '')
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      .replace(/\[\[([^\]]+)\]\]/g, '$1')
      .replace(/```[\s\S]*?```/g, '')
      .replace(/`[^`]+`/g, '')
      .replace(/\n+/g, ' ')
      .trim();
    return plainText.substring(0, 120) + (plainText.length > 120 ? '...' : '');
  }, [note.content]);

  // Format creation date as short absolute (e.g., "Jan 15")
  const createdDate = useMemo(() => {
    if (!note.created_at) return null;
    const date = new Date(note.created_at);
    const now = new Date();
    const sameYear = date.getFullYear() === now.getFullYear();
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      ...(sameYear ? {} : { year: '2-digit' })
    });
  }, [note.created_at]);

  // Format modification as relative time (only if different from created)
  const modifiedTime = useMemo(() => {
    if (!note.updated_at || !note.created_at) return null;
    const created = new Date(note.created_at);
    const updated = new Date(note.updated_at);
    // Consider "same" if within 60 seconds
    if (Math.abs(updated - created) < 60000) return null;

    const now = new Date();
    const diffMs = now - updated;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return updated.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }, [note.updated_at, note.created_at]);

  // Highlight search terms in text
  const highlightText = (text, query) => {
    if (!query?.trim() || !text) return text;
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const parts = text.split(regex);
    return parts.map((part, i) =>
      regex.test(part) ? <mark key={i} className="search-highlight">{part}</mark> : part
    );
  };

  // Type badge config with labels
  const typeBadges = {
    doc_ai: { icon: FileText, label: 'Doc AI', className: 'badge-doc-ai' },
    photo_ai: { icon: Camera, label: 'Photo AI', className: 'badge-photo-ai' },
    daily: { icon: Calendar, label: 'Daily', className: 'badge-daily' },
    manual: { icon: FileText, label: 'Note', className: 'badge-manual' }
  };

  const badge = typeBadges[noteType];
  const BadgeIcon = badge.icon;

  return (
    <article
      className={`note-card ${isSelected ? 'selected' : ''}`}
      onClick={onClick}
      onDoubleClick={onDoubleClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter') onClick();
        if (e.key === ' ') { e.preventDefault(); onClick(); }
      }}
    >
      {/* Header with title and badge */}
      <header className="note-card-header">
        <h3 className="note-card-title">
          {highlightText(note.title || 'Untitled', searchQuery)}
        </h3>
        <span className={`note-card-badge ${badge.className}`} title={badge.label}>
          <BadgeIcon size={12} />
          <span className="badge-label">{badge.label}</span>
        </span>
      </header>

      {/* Content preview */}
      <p className="note-card-excerpt">
        {highlightText(excerpt, searchQuery) || <span className="empty-note">Empty note</span>}
      </p>

      {/* Image indicator */}
      {note.image_ids && note.image_ids.length > 0 && (
        <div className="note-card-images">
          <Image size={14} />
          <span>{note.image_ids.length} image{note.image_ids.length > 1 ? 's' : ''}</span>
        </div>
      )}

      {/* Tags */}
      {note.tags && note.tags.length > 0 && (
        <div className="note-card-tags">
          {note.tags.slice(0, 3).map(tag => (
            <span key={tag.id || tag.name} className="note-tag">
              <Hash size={10} />
              {tag.name}
            </span>
          ))}
          {note.tags.length > 3 && (
            <span className="note-tag more">+{note.tags.length - 3}</span>
          )}
        </div>
      )}

      {/* Footer with dates and links */}
      <footer className="note-card-footer">
        <span className="note-card-dates">
          {createdDate && (
            <span className="note-card-created">
              <Clock size={11} />
              {createdDate}
            </span>
          )}
          {modifiedTime && (
            <span className="note-card-modified">
              &middot; edited {modifiedTime}
            </span>
          )}
        </span>
        {(note.linked_notes?.length > 0 || note.backlinks?.length > 0) && (
          <span className="note-card-links">
            <ExternalLink size={12} />
            {(note.linked_notes?.length || 0) + (note.backlinks?.length || 0)}
          </span>
        )}
      </footer>
    </article>
  );
}

export default NoteCard;
