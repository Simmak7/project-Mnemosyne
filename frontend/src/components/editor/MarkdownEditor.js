import React, { useState, useEffect, useCallback, useRef } from 'react';
import MDEditor from '@uiw/react-md-editor';
import { FiSave, FiX, FiExternalLink } from 'react-icons/fi';
import useDebounce from '../../hooks/useDebounce';
import WikilinkAutocomplete from './WikilinkAutocomplete';
import TagSelector from './TagSelector';
import EditorToolbar from './EditorToolbar';
import { API_URL } from '../../utils/api';
import './MarkdownEditor.css';

/**
 * Split-panel markdown editor with live preview
 *
 * Features:
 * - Split view: Editor | Preview
 * - Wikilink autocomplete on [[ trigger
 * - Tag selector with counts
 * - Auto-save (2s debounce)
 * - Toolbar with formatting buttons
 * - Keyboard shortcuts
 */
function MarkdownEditor({ noteId, initialNote, onSave, onClose }) {
  const [title, setTitle] = useState(initialNote?.title || '');
  const [content, setContent] = useState(initialNote?.content || '');
  const [tags, setTags] = useState(initialNote?.tags || []);
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState(null);
  const [isDirty, setIsDirty] = useState(false);

  // Wikilink autocomplete state
  const [showAutocomplete, setShowAutocomplete] = useState(false);
  const [autocompletePosition, setAutocompletePosition] = useState({ top: 0, left: 0 });
  const [wikilinkQuery, setWikilinkQuery] = useState('');
  const [cursorPosition, setCursorPosition] = useState(0);

  const editorRef = useRef(null);
  const debouncedContent = useDebounce(content, 2000);
  const debouncedTitle = useDebounce(title, 2000);

  // Auto-save when content/title changes
  useEffect(() => {
    if (isDirty && (debouncedContent || debouncedTitle)) {
      handleAutoSave();
    }
  }, [debouncedContent, debouncedTitle]);

  // Mark as dirty when user edits
  useEffect(() => {
    if (title !== initialNote?.title || content !== initialNote?.content) {
      setIsDirty(true);
    }
  }, [title, content, initialNote]);

  // Auto-save function
  const handleAutoSave = async () => {
    if (!isDirty) return;

    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      const url = noteId
        ? `${API_URL}/notes/${noteId}`
        : `${API_URL}/notes/`;

      const method = noteId ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          title: title || 'Untitled Note',
          content,
          tags: tags.map(t => typeof t === 'string' ? t : t.name),
        }),
      });

      if (response.ok) {
        const savedNote = await response.json();
        setLastSaved(new Date());
        setIsDirty(false);
        if (onSave) onSave(savedNote);
      } else {
        console.error('Failed to save note');
      }
    } catch (error) {
      console.error('Error saving note:', error);
    } finally {
      setSaving(false);
    }
  };

  // Manual save (Ctrl+S)
  const handleManualSave = useCallback(() => {
    handleAutoSave();
  }, [handleAutoSave]);

  // Detect [[ for wikilink autocomplete
  const handleContentChange = (value) => {
    setContent(value || '');

    // Detect [[ trigger
    const textarea = editorRef.current?.querySelector('textarea');
    if (!textarea) return;

    const cursorPos = textarea.selectionStart;
    const textBeforeCursor = value.substring(0, cursorPos);
    const lastDoubleBracket = textBeforeCursor.lastIndexOf('[[');

    if (lastDoubleBracket !== -1) {
      const textAfterBracket = textBeforeCursor.substring(lastDoubleBracket + 2);

      // Check if there's a closing ]]
      if (!textAfterBracket.includes(']]')) {
        // Show autocomplete
        setWikilinkQuery(textAfterBracket);
        setShowAutocomplete(true);
        setCursorPosition(lastDoubleBracket);

        // Calculate position for autocomplete dropdown
        const rect = textarea.getBoundingClientRect();
        const lineHeight = 20; // Approximate
        const lines = textBeforeCursor.split('\n').length;
        setAutocompletePosition({
          top: rect.top + (lines * lineHeight),
          left: rect.left + 20,
        });
      } else {
        setShowAutocomplete(false);
      }
    } else {
      setShowAutocomplete(false);
    }
  };

  // Insert wikilink when selected from autocomplete
  const handleWikilinkSelect = (note) => {
    const beforeCursor = content.substring(0, cursorPosition);
    const afterCursor = content.substring(cursorPosition + 2 + wikilinkQuery.length);
    const newContent = beforeCursor + `[[${note.title}]]` + afterCursor;

    setContent(newContent);
    setShowAutocomplete(false);
    setWikilinkQuery('');
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ctrl+S or Cmd+S to save
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        handleManualSave();
      }

      // Escape to close
      if (e.key === 'Escape' && !showAutocomplete) {
        if (onClose) onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleManualSave, showAutocomplete, onClose]);

  // Format last saved time
  const formatLastSaved = () => {
    if (!lastSaved) return 'Not saved';
    const seconds = Math.floor((new Date() - lastSaved) / 1000);
    if (seconds < 5) return 'Just now';
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    return lastSaved.toLocaleTimeString();
  };

  return (
    <div className="markdown-editor-container">
      {/* Header */}
      <div className="editor-header">
        <input
          type="text"
          className="editor-title-input"
          placeholder="Untitled Note"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <div className="editor-header-actions">
          <span className="save-status">
            {saving && '💾 Saving...'}
            {!saving && isDirty && '✏️ Unsaved changes'}
            {!saving && !isDirty && lastSaved && `✓ ${formatLastSaved()}`}
          </span>
          <button
            className="manual-save-button"
            onClick={handleManualSave}
            disabled={saving || !isDirty}
            title="Save (Ctrl+S)"
          >
            <FiSave />
          </button>
          {onClose && (
            <button className="close-button" onClick={onClose} title="Close (Esc)">
              <FiX />
            </button>
          )}
        </div>
      </div>

      {/* Tag Selector */}
      <div className="editor-tags-section">
        <TagSelector
          selectedTags={tags}
          onChange={setTags}
        />
      </div>

      {/* Editor Toolbar */}
      <EditorToolbar
        onInsert={(text) => setContent(content + text)}
        onFormat={(format) => {
          // Handle formatting (bold, italic, etc.)
          // This is a simplified version
          const selection = window.getSelection().toString();
          if (selection) {
            const newContent = content.replace(selection, `${format}${selection}${format}`);
            setContent(newContent);
          }
        }}
      />

      {/* Split Panel Editor */}
      <div className="editor-content" ref={editorRef}>
        <MDEditor
          value={content}
          onChange={handleContentChange}
          preview="live"
          height={600}
          highlightEnable={true}
          enableScroll={true}
          visibleDragbar={true}
        />
      </div>

      {/* Wikilink Autocomplete */}
      {showAutocomplete && (
        <WikilinkAutocomplete
          query={wikilinkQuery}
          onSelect={handleWikilinkSelect}
          onClose={() => setShowAutocomplete(false)}
          position={autocompletePosition}
        />
      )}

      {/* Footer Info */}
      <div className="editor-footer">
        <div className="editor-stats">
          <span>{content.length} characters</span>
          <span>•</span>
          <span>{content.split(/\s+/).filter(w => w).length} words</span>
          <span>•</span>
          <span>{content.split('\n').length} lines</span>
        </div>
        <div className="editor-shortcuts">
          <span className="shortcut-hint">
            <FiSave /> Ctrl+S to save
          </span>
          <span className="shortcut-hint">
            <FiExternalLink /> [[ for wikilink
          </span>
        </div>
      </div>
    </div>
  );
}

export default MarkdownEditor;
