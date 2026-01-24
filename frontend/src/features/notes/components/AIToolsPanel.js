import React, { useState, useCallback } from 'react';
import {
  Sparkles,
  Type,
  FileText,
  Link2,
  RefreshCw,
  Check,
  Copy,
  ArrowRight,
  Wand2,
  Image,
  AlertCircle
} from 'lucide-react';
import './AIToolsPanel.css';

const API_BASE = 'http://localhost:8000';

/**
 * AIToolsPanel - AI enhancement tools for notes
 * Features: Improve Title, Summarize, Suggest Wikilinks
 */
function AIToolsPanel({ note, onTitleUpdate, onNavigateToNote, onRefreshNote }) {
  const [loading, setLoading] = useState({});
  const [results, setResults] = useState({});
  const [errors, setErrors] = useState({});

  // API call helper
  const callAI = useCallback(async (endpoint, key) => {
    setLoading(prev => ({ ...prev, [key]: true }));
    setErrors(prev => ({ ...prev, [key]: null }));

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/notes/${note.id}/${endpoint}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'AI service error');
      }

      const data = await response.json();
      setResults(prev => ({ ...prev, [key]: data }));
      return data;
    } catch (err) {
      setErrors(prev => ({ ...prev, [key]: err.message }));
      throw err;
    } finally {
      setLoading(prev => ({ ...prev, [key]: false }));
    }
  }, [note.id]);

  // Improve title
  const handleImproveTitle = useCallback(async () => {
    await callAI('improve-title', 'title');
  }, [callAI]);

  // Apply improved title
  const applyTitle = useCallback(async () => {
    if (!results.title?.improved_title) return;

    try {
      const token = localStorage.getItem('token');
      await fetch(`${API_BASE}/notes/${note.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          title: results.title.improved_title,
          content: note.content
        })
      });

      if (onTitleUpdate) {
        onTitleUpdate(results.title.improved_title);
      }
      setResults(prev => ({ ...prev, title: { ...prev.title, applied: true } }));
    } catch (err) {
      setErrors(prev => ({ ...prev, title: 'Failed to apply title' }));
    }
  }, [note.id, note.content, results.title, onTitleUpdate]);

  // Summarize
  const handleSummarize = useCallback(async () => {
    await callAI('summarize', 'summary');
  }, [callAI]);

  // Copy summary to clipboard
  const copySummary = useCallback(() => {
    if (results.summary?.summary) {
      navigator.clipboard.writeText(results.summary.summary);
      setResults(prev => ({ ...prev, summary: { ...prev.summary, copied: true } }));
      setTimeout(() => {
        setResults(prev => ({ ...prev, summary: { ...prev.summary, copied: false } }));
      }, 2000);
    }
  }, [results.summary]);

  // Suggest wikilinks
  const handleSuggestWikilinks = useCallback(async () => {
    await callAI('suggest-wikilinks', 'wikilinks');
  }, [callAI]);

  // Regenerate from source
  const handleRegenerate = useCallback(async () => {
    // Check if note has linked images
    if (!note.image_ids || note.image_ids.length === 0) {
      setErrors(prev => ({ ...prev, regenerate: 'This note has no linked images to regenerate from' }));
      return;
    }

    setLoading(prev => ({ ...prev, regenerate: true }));
    setErrors(prev => ({ ...prev, regenerate: null }));

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/notes/${note.id}/regenerate?apply=true`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMsg = errorData.detail || errorData.message || 'Failed to regenerate';
        throw new Error(errorMsg);
      }

      const data = await response.json();
      setResults(prev => ({ ...prev, regenerate: data }));

      // Trigger page refresh to show new content
      window.location.reload();
    } catch (err) {
      setErrors(prev => ({ ...prev, regenerate: err.message }));
    } finally {
      setLoading(prev => ({ ...prev, regenerate: false }));
    }
  }, [note.id, note.image_ids]);

  // Insert wikilink into note content
  const handleInsertWikilink = useCallback(async (noteTitle, suggestionIdx) => {
    const wikilinkText = `[[${noteTitle}]]`;

    try {
      const token = localStorage.getItem('token');
      // Append wikilink to the end of the note content
      const newContent = (note.content || '') + (note.content ? '\n\n' : '') + wikilinkText;

      const response = await fetch(`${API_BASE}/notes/${note.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          title: note.title,
          content: newContent
        })
      });

      if (response.ok) {
        // Mark this suggestion as added
        setResults(prev => ({
          ...prev,
          wikilinks: {
            ...prev.wikilinks,
            suggestions: prev.wikilinks.suggestions.map((s, idx) =>
              idx === suggestionIdx ? { ...s, added: true } : s
            )
          }
        }));

        // Refresh the note to show updated linked_notes
        if (onRefreshNote) {
          onRefreshNote();
        }
      }
    } catch (err) {
      console.error('Failed to insert wikilink:', err);
    }
  }, [note.id, note.content, note.title, onRefreshNote]);

  // Check if note has linked images
  const hasLinkedImages = note.image_ids && note.image_ids.length > 0;
  const isAIGenerated = note.is_standalone === false;

  return (
    <div className="ai-tools-panel">
      {/* Enhance Knowledge Section */}
      <section className="ai-section">
        <h4 className="section-header">
          <Sparkles size={14} />
          Enhance Knowledge
        </h4>

        {/* Improve Title Tool */}
        <div className="ai-tool">
          <button
            className="ai-tool-btn"
            onClick={handleImproveTitle}
            disabled={loading.title}
          >
            <Type size={16} />
            <span>Improve Title</span>
            {loading.title && <RefreshCw size={14} className="spin" />}
          </button>

          {results.title && !results.title.applied && (
            <div className="ai-result">
              <div className="result-content">
                <span className="result-label">Suggested:</span>
                <span className="result-value">{results.title.improved_title}</span>
              </div>
              <div className="result-actions">
                <button className="action-btn apply" onClick={applyTitle}>
                  <Check size={12} />
                  Apply
                </button>
              </div>
            </div>
          )}

          {results.title?.applied && (
            <div className="ai-result success">
              <Check size={14} />
              <span>Title updated!</span>
            </div>
          )}

          {errors.title && (
            <div className="ai-error">
              <AlertCircle size={14} />
              <span>{errors.title}</span>
            </div>
          )}
        </div>

        {/* Summarize Tool */}
        <div className="ai-tool">
          <button
            className="ai-tool-btn"
            onClick={handleSummarize}
            disabled={loading.summary}
          >
            <FileText size={16} />
            <span>Summarize</span>
            {loading.summary && <RefreshCw size={14} className="spin" />}
          </button>

          {results.summary?.summary && (
            <div className="ai-result">
              <div className="result-content summary">
                <p>{results.summary.summary}</p>
              </div>
              <div className="result-actions">
                <button className="action-btn" onClick={copySummary}>
                  {results.summary.copied ? <Check size={12} /> : <Copy size={12} />}
                  {results.summary.copied ? 'Copied!' : 'Copy'}
                </button>
              </div>
            </div>
          )}

          {errors.summary && (
            <div className="ai-error">
              <AlertCircle size={14} />
              <span>{errors.summary}</span>
            </div>
          )}
        </div>

        {/* Suggest Wikilinks Tool */}
        <div className="ai-tool">
          <button
            className="ai-tool-btn"
            onClick={handleSuggestWikilinks}
            disabled={loading.wikilinks}
          >
            <Link2 size={16} />
            <span>Suggest Wikilinks</span>
            {loading.wikilinks && <RefreshCw size={14} className="spin" />}
          </button>

          {results.wikilinks?.suggestions?.length > 0 && (
            <div className="ai-result wikilinks">
              <div className="result-label">Suggested connections:</div>
              <ul className="wikilink-suggestions">
                {results.wikilinks.suggestions.map((suggestion, idx) => (
                  <li key={idx}>
                    <button
                      className={`wikilink-btn ${suggestion.added ? 'added' : ''}`}
                      onClick={() => !suggestion.added && handleInsertWikilink(suggestion.title, idx)}
                      disabled={suggestion.added}
                    >
                      {suggestion.added ? (
                        <>
                          <Check size={12} />
                          <span className="wikilink-title">[[{suggestion.title}]]</span>
                          <span className="added-label">Added!</span>
                        </>
                      ) : (
                        <>
                          <Link2 size={12} />
                          <span className="wikilink-title">[[{suggestion.title}]]</span>
                          <span className="add-label">+ Add</span>
                        </>
                      )}
                    </button>
                    {suggestion.reason && (
                      <span className="wikilink-reason">{suggestion.reason}</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {results.wikilinks?.suggestions?.length === 0 && (
            <div className="ai-result empty">
              <span>No connection suggestions found</span>
            </div>
          )}

          {errors.wikilinks && (
            <div className="ai-error">
              <AlertCircle size={14} />
              <span>{errors.wikilinks}</span>
            </div>
          )}
        </div>
      </section>

      {/* Vision Analysis Section (for image-linked notes) */}
      {(hasLinkedImages || isAIGenerated) && (
        <section className="ai-section">
          <h4 className="section-header">
            <Image size={14} />
            Vision Analysis
          </h4>

          <div className="vision-info">
            {isAIGenerated ? (
              <p>This note was generated from an image using AI vision analysis.</p>
            ) : (
              <p>This note has {note.image_ids.length} linked image{note.image_ids.length > 1 ? 's' : ''}.</p>
            )}
          </div>

          <button
            className="ai-tool-btn"
            onClick={handleRegenerate}
            disabled={loading.regenerate}
          >
            <Wand2 size={16} />
            <span>Regenerate from Source</span>
            {loading.regenerate && <RefreshCw size={14} className="spin" />}
          </button>

          {results.regenerate && (
            <div className="ai-result success">
              <Check size={14} />
              <span>Content regenerated!</span>
            </div>
          )}

          {errors.regenerate && (
            <div className="ai-error">
              <AlertCircle size={14} />
              <span>{errors.regenerate}</span>
            </div>
          )}
        </section>
      )}

      {/* AI Status Footer */}
      <div className="ai-footer">
        <Sparkles size={12} />
        <span>Powered by local AI (Ollama)</span>
      </div>
    </div>
  );
}

export default AIToolsPanel;
