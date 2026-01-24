import React, { useMemo } from 'react';
import {
  Sparkles,
  Calendar,
  FileText,
  Heart,
  Network,
  Trash2,
  MoreHorizontal,
  CheckCircle,
  Pencil,
  RotateCcw,
  MessageSquare
} from 'lucide-react';
import CollectionPicker from './CollectionPicker';

/**
 * NoteDetailHeader - Header with title, metadata, and action buttons
 */
function NoteDetailHeader({
  note,
  onNavigateToGraph,
  onNavigateToAI,
  onToggleFavorite,
  onMoveToTrash,
  onToggleReviewed,
  onRestoreFromTrash,
  onEdit,
  isEditing
}) {
  // Determine note type
  const noteType = useMemo(() => {
    const hasImages = note.image_ids && note.image_ids.length > 0;
    const isDaily = note.title?.startsWith('Daily Note') ||
                    note.title?.match(/^\d{4}-\d{2}-\d{2}/);

    if (isDaily) return { label: 'Daily Note', icon: Calendar, className: 'type-daily' };
    if (hasImages || note.is_standalone === false) return { label: 'AI Source', icon: Sparkles, className: 'type-ai' };
    return { label: 'Manual', icon: FileText, className: 'type-manual' };
  }, [note]);

  const TypeIcon = noteType.icon;

  // Format dates
  const formatDate = (dateStr) => {
    if (!dateStr) return 'Unknown';
    const date = new Date(dateStr);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  // Calculate word count
  const wordCount = useMemo(() => {
    if (!note.content) return 0;
    return note.content.trim().split(/\s+/).filter(w => w.length > 0).length;
  }, [note.content]);

  return (
    <header className="note-detail-header">
      {/* Title */}
      <h1 className="note-title">{note.title || 'Untitled'}</h1>

      {/* Metadata row */}
      <div className="note-meta">
        <span className={`note-type ${noteType.className}`}>
          <TypeIcon size={12} />
          {noteType.label}
        </span>
        <span className="meta-separator">•</span>
        <span className="note-updated">Updated {formatDate(note.updated_at || note.created_at)}</span>
        <span className="meta-separator">•</span>
        <span className="note-word-count">{wordCount} words</span>
      </div>

      {/* Action buttons */}
      <div className="note-actions">
        {/* Edit note */}
        {onEdit && !isEditing && (
          <button
            className="action-btn action-primary"
            onClick={onEdit}
            title="Edit note"
          >
            <Pencil size={16} />
          </button>
        )}

        {/* Navigate to graph */}
        {onNavigateToGraph && (
          <button
            className="action-btn"
            onClick={() => onNavigateToGraph(note.id)}
            title="View in knowledge graph"
          >
            <Network size={16} />
          </button>
        )}

        {/* Ask AI about this note */}
        {onNavigateToAI && (
          <button
            className="action-btn action-ai"
            onClick={() => onNavigateToAI({ type: 'note', id: note.id, title: note.title })}
            title="Ask AI about this note"
          >
            <MessageSquare size={16} />
          </button>
        )}

        {/* Add to collection */}
        {!note.is_trashed && (
          <CollectionPicker noteId={note.id} />
        )}

        {/* Favorite toggle */}
        <button
          className={`action-btn ${note.is_favorite ? 'active' : ''}`}
          title={note.is_favorite ? 'Remove from favorites' : 'Add to favorites'}
          onClick={onToggleFavorite}
        >
          <Heart size={16} fill={note.is_favorite ? 'currentColor' : 'none'} />
        </button>

        {/* Mark reviewed */}
        <button
          className={`action-btn ${note.is_reviewed ? 'active' : ''}`}
          title={note.is_reviewed ? 'Reviewed' : 'Mark as reviewed'}
          onClick={onToggleReviewed}
        >
          <CheckCircle size={16} />
        </button>

        {/* Restore from trash OR Delete (move to trash) */}
        {note.is_trashed ? (
          <button
            className="action-btn action-success"
            title="Restore from trash"
            onClick={onRestoreFromTrash}
          >
            <RotateCcw size={16} />
          </button>
        ) : (
          <button
            className="action-btn action-danger"
            title="Move to trash"
            onClick={onMoveToTrash}
          >
            <Trash2 size={16} />
          </button>
        )}

        {/* More options */}
        <button className="action-btn" title="More options">
          <MoreHorizontal size={16} />
        </button>
      </div>
    </header>
  );
}

export default NoteDetailHeader;
