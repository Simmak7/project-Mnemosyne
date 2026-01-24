import React, { useEffect, useState } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import { Mention } from '@tiptap/extension-mention';
import { WikilinkExtension } from '../../extensions/WikilinkExtension';
import { HashtagExtension } from '../../extensions/HashtagExtension';
import { wikilinkSuggestion } from './WikilinkSuggestion';
import { hashtagSuggestion } from './HashtagSuggestion';
import { Save, X } from 'lucide-react';
import './TiptapEditor.css';

/**
 * TiptapEditor - Rich text editor with wikilink and hashtag autocomplete
 * @param {Object} props
 * @param {Object} props.note - Note object to edit
 * @param {Array} props.allNotes - All notes for wikilink autocomplete
 * @param {Array} props.allTags - All tags for hashtag autocomplete
 * @param {Function} props.onSave - Callback when save is clicked
 * @param {Function} props.onCancel - Callback when cancel is clicked
 * @param {Function} props.onWikilinkClick - Callback when wikilink is clicked
 * @param {Function} props.onHashtagClick - Callback when hashtag is clicked
 * @param {Function} props.onEditorReady - Callback when editor instance is ready (Phase 4)
 */
function TiptapEditor({
  note,
  allNotes = [],
  allTags = [],
  onSave,
  onCancel,
  onWikilinkClick,
  onHashtagClick,
  onEditorReady
}) {
  const [title, setTitle] = useState(note?.title || '');
  const [hasChanges, setHasChanges] = useState(false);

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: {
          levels: [1, 2, 3],
        },
      }),
      Placeholder.configure({
        placeholder: 'Start typing... Use [[ for wikilinks or # for tags',
      }),
      WikilinkExtension,
      HashtagExtension,
      Mention.configure({
        HTMLAttributes: {
          class: 'mention-wikilink',
        },
        suggestion: wikilinkSuggestion(allNotes),
      }),
      Mention.extend({ name: 'hashtagMention' }).configure({
        HTMLAttributes: {
          class: 'mention-hashtag',
        },
        suggestion: hashtagSuggestion(allTags),
      }),
    ],
    content: note?.content || '',
    editorProps: {
      attributes: {
        class: 'tiptap-editor-content',
      },
    },
    onUpdate: () => {
      setHasChanges(true);
    },
    onCreate: ({ editor: editorInstance }) => {
      // Notify parent component that editor is ready (Phase 4)
      if (onEditorReady) {
        onEditorReady(editorInstance);
      }
    },
  });

  // Update editor content when note changes
  useEffect(() => {
    if (editor && note) {
      setTitle(note.title || '');
      editor.commands.setContent(note.content || '');
      setHasChanges(false);
    }
  }, [note?.id, editor]);

  // Handle wikilink clicks
  useEffect(() => {
    if (!editor || !onWikilinkClick) return;

    const handleWikilinkClick = (event) => {
      if (event.detail && event.detail.title) {
        onWikilinkClick(event.detail.title);
      }
    };

    editor.view.dom.addEventListener('wikilink-click', handleWikilinkClick);

    return () => {
      editor.view.dom.removeEventListener('wikilink-click', handleWikilinkClick);
    };
  }, [editor, onWikilinkClick]);

  // Handle hashtag clicks
  useEffect(() => {
    if (!editor || !onHashtagClick) return;

    const handleHashtagClick = (event) => {
      if (event.detail && event.detail.tag) {
        onHashtagClick(event.detail.tag);
      }
    };

    editor.view.dom.addEventListener('hashtag-click', handleHashtagClick);

    return () => {
      editor.view.dom.removeEventListener('hashtag-click', handleHashtagClick);
    };
  }, [editor, onHashtagClick]);

  const handleSave = () => {
    if (!editor) return;

    const htmlContent = editor.getHTML();

    // Convert HTML to markdown with wikilinks and hashtags preserved
    let markdownContent = htmlContent;

    // Replace wikilink spans with [[title]] syntax
    markdownContent = markdownContent.replace(
      /<span[^>]*data-wikilink-title="([^"]+)"[^>]*>[^<]*<\/span>/g,
      '[[$1]]'
    );

    // Replace hashtag spans with #tag syntax
    markdownContent = markdownContent.replace(
      /<span[^>]*data-hashtag="([^"]+)"[^>]*>#[^<]*<\/span>/g,
      '#$1'
    );

    // Remove HTML tags to get clean text with wikilinks and hashtags
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = markdownContent;
    const textContent = tempDiv.textContent || tempDiv.innerText || '';

    // Extract wikilinks for metadata
    const wikilinkMatches = htmlContent.matchAll(/data-wikilink-title="([^"]+)"/g);
    const wikilinks = [...wikilinkMatches].map(match => match[1]);

    // Extract hashtags for metadata
    const hashtagMatches = htmlContent.matchAll(/data-hashtag="([^"]+)"/g);
    const tags = [...hashtagMatches].map(match => match[1]);

    onSave({
      title,
      content: textContent, // Content with [[wikilinks]] and #hashtags preserved
      html: htmlContent,
      wikilinks: [...new Set(wikilinks)],
      tags: [...new Set(tags)],
    });

    setHasChanges(false);
  };

  const handleCancel = () => {
    if (hasChanges) {
      if (window.confirm('You have unsaved changes. Discard them?')) {
        onCancel();
      }
    } else {
      onCancel();
    }
  };

  if (!editor) {
    return <div className="tiptap-editor-loading">Loading editor...</div>;
  }

  return (
    <div className="tiptap-editor-container">
      {/* Toolbar */}
      <div className="tiptap-toolbar">
        <input
          type="text"
          className="tiptap-title-input"
          value={title}
          onChange={(e) => {
            setTitle(e.target.value);
            setHasChanges(true);
          }}
          placeholder="Untitled"
        />

        <div className="tiptap-toolbar-buttons">
          <button
            onClick={handleSave}
            className="tiptap-btn tiptap-btn-save"
            disabled={!hasChanges}
          >
            <Save size={16} />
            Save
          </button>
          <button
            onClick={handleCancel}
            className="tiptap-btn tiptap-btn-cancel"
          >
            <X size={16} />
            Cancel
          </button>
        </div>
      </div>

      {/* Format toolbar */}
      <div className="tiptap-format-toolbar">
        <button
          onClick={() => editor.chain().focus().toggleBold().run()}
          className={editor.isActive('bold') ? 'active' : ''}
        >
          <strong>B</strong>
        </button>
        <button
          onClick={() => editor.chain().focus().toggleItalic().run()}
          className={editor.isActive('italic') ? 'active' : ''}
        >
          <em>I</em>
        </button>
        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
          className={editor.isActive('heading', { level: 1 }) ? 'active' : ''}
        >
          H1
        </button>
        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          className={editor.isActive('heading', { level: 2 }) ? 'active' : ''}
        >
          H2
        </button>
        <button
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          className={editor.isActive('bulletList') ? 'active' : ''}
        >
          • List
        </button>
        <button
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          className={editor.isActive('orderedList') ? 'active' : ''}
        >
          1. List
        </button>
        <button
          onClick={() => editor.chain().focus().toggleCodeBlock().run()}
          className={editor.isActive('codeBlock') ? 'active' : ''}
        >
          &lt;/&gt; Code
        </button>
      </div>

      {/* Editor content */}
      <EditorContent editor={editor} className="tiptap-editor" />

      {/* Hints */}
      <div className="tiptap-hints">
        <span>💡 Tip: Type <code>[[</code> for wikilinks or <code>#</code> for tags</span>
        {hasChanges && <span className="tiptap-unsaved">● Unsaved changes</span>}
      </div>
    </div>
  );
}

export default TiptapEditor;
