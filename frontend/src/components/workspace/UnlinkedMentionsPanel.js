import React, { useState, useEffect } from 'react';
import { Search, Link2, AlertCircle, Loader, Check } from 'lucide-react';
import { useWorkspaceState } from '../../hooks/useWorkspaceState';
import './ContextPanels.css';

/**
 * UnlinkedMentionsPanel - Phase 3 Semantic Search
 *
 * Displays notes that are semantically similar to the current note
 * but don't have wikilinks to it. Helps users discover potential connections.
 */
function UnlinkedMentionsPanel() {
  const { selectedNoteId, triggerNoteRefresh } = useWorkspaceState();
  const [mentions, setMentions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [threshold, setThreshold] = useState(0.7);
  const [noteTitle, setNoteTitle] = useState('');
  const [linkingId, setLinkingId] = useState(null); // Track which mention is being linked
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    if (selectedNoteId) {
      fetchUnlinkedMentions();
    } else {
      setMentions([]);
      setNoteTitle('');
    }
  }, [selectedNoteId, threshold]);

  const fetchUnlinkedMentions = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `http://localhost:8000/search/notes/${selectedNoteId}/unlinked-mentions?limit=10&threshold=${threshold}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (!response.ok) {
        if (response.status === 400) {
          const data = await response.json();
          throw new Error(data.detail || 'Note does not have an embedding yet');
        }
        throw new Error('Failed to fetch unlinked mentions');
      }

      const data = await response.json();
      setMentions(data.results || []);
      setNoteTitle(data.note_title || '');
    } catch (err) {
      setError(err.message);
      setMentions([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAddLink = async (mentionId, mentionTitle) => {
    // Get current note content
    const token = localStorage.getItem('token');
    setLinkingId(mentionId);
    setSuccessMessage('');

    try {
      // Fetch current note
      const noteResponse = await fetch(
        `http://localhost:8000/notes/${selectedNoteId}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (!noteResponse.ok) {
        throw new Error('Failed to fetch note');
      }

      const note = await noteResponse.json();

      // Add wikilink at the end of content
      const wikilink = `[[${mentionTitle}]]`;
      const updatedContent = `${note.content}\n\n${wikilink}`;

      // Update note
      const updateResponse = await fetch(
        `http://localhost:8000/notes/${selectedNoteId}`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            title: note.title,
            content: updatedContent
          })
        }
      );

      if (!updateResponse.ok) {
        throw new Error('Failed to update note');
      }

      // Trigger refresh in CenterPane to show updated content
      triggerNoteRefresh();

      // Refresh unlinked mentions (the added link will be filtered out)
      fetchUnlinkedMentions();

      // Show success message
      setSuccessMessage(`Linked to "${mentionTitle}"`);
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err) {
      setError(`Failed to add link: ${err.message}`);
      setTimeout(() => setError(null), 5000);
    } finally {
      setLinkingId(null);
    }
  };

  const formatSimilarity = (similarity) => {
    return `${Math.round(similarity * 100)}%`;
  };

  if (!selectedNoteId) {
    return (
      <div className="panel-placeholder">
        <Search size={48} className="placeholder-icon" />
        <h3>Unlinked Mentions</h3>
        <p>Select a note to discover potential connections</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="panel-loading">
        <Loader size={24} className="spinner" />
        <p>Finding similar notes...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="panel-error">
        <AlertCircle size={24} />
        <p>{error}</p>
        {error.includes('embedding') && (
          <small>Wait a moment for embedding generation to complete</small>
        )}
      </div>
    );
  }

  return (
    <div className="unlinked-mentions-panel">
      <div className="panel-header">
        <h3>Unlinked Mentions</h3>
        <div className="threshold-control">
          <label>
            Threshold: {Math.round(threshold * 100)}%
          </label>
          <input
            type="range"
            min="0.5"
            max="0.95"
            step="0.05"
            value={threshold}
            onChange={(e) => setThreshold(parseFloat(e.target.value))}
          />
        </div>
      </div>

      {/* Success message */}
      {successMessage && (
        <div className="panel-success">
          <Check size={16} />
          <span>{successMessage}</span>
        </div>
      )}

      {mentions.length === 0 ? (
        <div className="panel-empty">
          <p>No unlinked mentions found</p>
          <small>Try lowering the similarity threshold</small>
        </div>
      ) : (
        <div className="mentions-list">
          {mentions.map((mention) => (
            <div key={mention.id} className="mention-item">
              <div className="mention-header">
                <span className="mention-title">{mention.title}</span>
                <span className="mention-similarity">
                  {formatSimilarity(mention.similarity)}
                </span>
              </div>
              <p className="mention-snippet">{mention.snippet}</p>
              <button
                className="add-link-button"
                onClick={() => handleAddLink(mention.id, mention.title)}
                title="Add wikilink to current note"
                disabled={linkingId === mention.id}
              >
                {linkingId === mention.id ? (
                  <>
                    <Loader size={14} className="spinner" />
                    Linking...
                  </>
                ) : (
                  <>
                    <Link2 size={14} />
                    Add Link
                  </>
                )}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default UnlinkedMentionsPanel;
