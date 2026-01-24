import React, { useEffect, useState } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import TaskList from '@tiptap/extension-task-list';
import TaskItem from '@tiptap/extension-task-item';
import { Mention } from '@tiptap/extension-mention';
import { WikilinkExtension } from '../../../extensions/WikilinkExtension';
import { HashtagExtension } from '../../../extensions/HashtagExtension';
import { SlashCommandExtension } from '../extensions/SlashCommandExtension';
import { configureSlashCommands } from '../hooks/useSlashCommands';
import { wikilinkSuggestion } from '../../../components/editor/WikilinkSuggestion';
import { hashtagSuggestion } from '../../../components/editor/HashtagSuggestion';
import { Save, X, Eye, EyeOff } from 'lucide-react';
import 'tippy.js/dist/tippy.css';
import './BlockEditor.css';

/**
 * BlockEditor - Enhanced TiptapEditor with slash commands and Neural Glass styling
 * Features: Slash command menu, rich typography, styled wikilinks/hashtags
 */
function BlockEditor({
  note,
  allNotes = [],
  allTags = [],
  onSave,
  onCancel,
  onWikilinkClick,
  onHashtagClick,
  onEditorReady,
}) {
  const [title, setTitle] = useState(note?.title || '');
  const [hasChanges, setHasChanges] = useState(false);
  const [isPreview, setIsPreview] = useState(false);

  // Convert plain text wikilinks [[Title]] to proper span elements
  const convertWikilinks = (html) => {
    // Match [[Title]] or [[Title|Alias]] patterns, but not already converted ones
    return html.replace(
      /(?<!data-wikilink-title="[^"]*)\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g,
      (match, title, alias) => {
        const displayText = alias || title;
        const aliasAttr = alias ? ` data-wikilink-alias="${alias}"` : '';
        return `<span data-wikilink-title="${title}"${aliasAttr} class="wikilink-chip" contenteditable="false">[[${displayText}]]</span>`;
      }
    );
  };

  // Convert plain text hashtags #tag to proper span elements
  const convertHashtags = (html) => {
    // Match #tag patterns (alphanumeric, underscores, hyphens), but not already converted ones
    // Avoid matching inside data-hashtag attributes or inside existing spans
    return html.replace(
      /(?<!data-hashtag="|class="|>)#([a-zA-Z][a-zA-Z0-9_-]*)/g,
      (match, tag) => {
        return `<span data-hashtag="${tag}" class="hashtag-chip" contenteditable="false">#${tag}</span>`;
      }
    );
  };

  // Convert plain text to HTML if needed (preserves line breaks, paragraphs, and task lists)
  const convertPlainTextToHtml = (text) => {
    if (!text) return '';
    // If it already looks like HTML, return as-is
    if (text.includes('<p>') || text.includes('<h') || text.includes('<ul>') || text.includes('<br')) {
      return text;
    }

    // Split into lines to detect task lists and regular paragraphs
    const lines = text.split('\n');
    const result = [];
    let inTaskList = false;
    let currentParagraph = [];

    const flushParagraph = () => {
      if (currentParagraph.length > 0) {
        const content = currentParagraph.join('<br>');
        result.push(`<p>${content}</p>`);
        currentParagraph = [];
      }
    };

    const flushTaskList = () => {
      if (inTaskList) {
        result.push('</ul>');
        inTaskList = false;
      }
    };

    for (const line of lines) {
      const trimmed = line.trim();

      // Check for task list item: - [x] or - [ ]
      const taskMatch = trimmed.match(/^-\s*\[([ xX])\]\s*(.*)$/);
      if (taskMatch) {
        flushParagraph();
        if (!inTaskList) {
          result.push('<ul data-type="taskList">');
          inTaskList = true;
        }
        const checked = taskMatch[1].toLowerCase() === 'x';
        const taskContent = taskMatch[2];
        result.push(`<li data-type="taskItem" data-checked="${checked}"><label><input type="checkbox" ${checked ? 'checked' : ''}><span></span></label><div><p>${taskContent}</p></div></li>`);
        continue;
      }

      // Check for regular list item: - text
      const listMatch = trimmed.match(/^-\s+(.+)$/);
      if (listMatch && !trimmed.match(/^-\s*\[/)) {
        flushParagraph();
        flushTaskList();
        // Regular bullet list (simple conversion)
        result.push(`<ul><li><p>${listMatch[1]}</p></li></ul>`);
        continue;
      }

      // Empty line marks paragraph break
      if (trimmed === '') {
        flushTaskList();
        flushParagraph();
        continue;
      }

      // Regular text - accumulate into paragraph
      flushTaskList();
      currentParagraph.push(trimmed);
    }

    // Flush remaining content
    flushTaskList();
    flushParagraph();

    return result.join('');
  };

  // Process content to recognize wikilinks and hashtags
  const processContentForEditor = (content) => {
    if (!content) return '';
    let html = convertPlainTextToHtml(content);
    // Convert plain text wikilinks and hashtags to proper nodes
    html = convertWikilinks(html);
    html = convertHashtags(html);
    return html;
  };

  // Get initial content for editor
  const getInitialContent = () => {
    if (note?.html_content) {
      // Even HTML content might have plain text wikilinks/hashtags from AI
      let html = note.html_content;
      html = convertWikilinks(html);
      html = convertHashtags(html);
      return html;
    }
    return processContentForEditor(note?.content || '');
  };

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: { levels: [1, 2, 3] },
      }),
      Placeholder.configure({
        placeholder: ({ node }) => {
          if (node.type.name === 'heading') {
            return 'Heading...';
          }
          return 'Type / for commands, [[ for notes, # for tags';
        },
      }),
      TaskList,
      TaskItem.configure({
        nested: true,
      }),
      WikilinkExtension,
      HashtagExtension,
      Mention.configure({
        HTMLAttributes: { class: 'mention-wikilink' },
        suggestion: wikilinkSuggestion(allNotes),
      }),
      Mention.extend({ name: 'hashtagMention' }).configure({
        HTMLAttributes: { class: 'mention-hashtag' },
        suggestion: hashtagSuggestion(allTags),
      }),
      configureSlashCommands(SlashCommandExtension),
    ],
    content: getInitialContent(),
    editorProps: {
      attributes: {
        class: 'ng-block-editor-content',
      },
    },
    onUpdate: () => {
      setHasChanges(true);
    },
    onCreate: ({ editor: editorInstance }) => {
      if (onEditorReady) {
        onEditorReady(editorInstance);
      }
    },
  });

  // Update editor when note changes
  useEffect(() => {
    if (editor && note) {
      setTitle(note.title || '');
      // Process content to convert plain text wikilinks/hashtags to proper nodes
      let content = note.html_content || convertPlainTextToHtml(note.content || '');
      content = convertWikilinks(content);
      content = convertHashtags(content);
      editor.commands.setContent(content);
      setHasChanges(false);
    }
  }, [note?.id, editor]);

  // Handle wikilink clicks
  useEffect(() => {
    if (!editor || !onWikilinkClick) return;

    const handleWikilinkClick = (event) => {
      if (event.detail?.title) {
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
      if (event.detail?.tag) {
        onHashtagClick(event.detail.tag);
      }
    };

    editor.view.dom.addEventListener('hashtag-click', handleHashtagClick);
    return () => {
      editor.view.dom.removeEventListener('hashtag-click', handleHashtagClick);
    };
  }, [editor, onHashtagClick]);

  // Convert HTML to plain text while preserving line breaks
  const htmlToPlainText = (html) => {
    // First, convert wikilinks and hashtags back to plain text format
    let processed = html;
    processed = processed.replace(
      /<span[^>]*data-wikilink-title="([^"]+)"[^>]*>[^<]*<\/span>/g,
      '[[$1]]'
    );
    processed = processed.replace(
      /<span[^>]*data-hashtag="([^"]+)"[^>]*>#[^<]*<\/span>/g,
      '#$1'
    );

    // Handle task lists (checkboxes)
    processed = processed.replace(
      /<li[^>]*data-checked="true"[^>]*>(.*?)<\/li>/gi,
      '- [x] $1\n'
    );
    processed = processed.replace(
      /<li[^>]*data-checked="false"[^>]*>(.*?)<\/li>/gi,
      '- [ ] $1\n'
    );

    // Convert block elements to proper line breaks
    processed = processed.replace(/<\/p>\s*<p[^>]*>/gi, '\n\n'); // Paragraph breaks
    processed = processed.replace(/<br\s*\/?>/gi, '\n'); // Line breaks
    processed = processed.replace(/<\/h[1-6]>/gi, '\n\n'); // After headings
    processed = processed.replace(/<h[1-6][^>]*>/gi, ''); // Remove heading tags
    processed = processed.replace(/<\/li>/gi, '\n'); // List items
    processed = processed.replace(/<li[^>]*>/gi, '- '); // List item markers
    processed = processed.replace(/<\/(ul|ol)>/gi, '\n'); // End of lists
    processed = processed.replace(/<(ul|ol)[^>]*>/gi, ''); // Remove list container tags
    processed = processed.replace(/<\/blockquote>/gi, '\n'); // After blockquotes
    processed = processed.replace(/<blockquote[^>]*>/gi, '> '); // Blockquote markers
    processed = processed.replace(/<\/div>/gi, '\n'); // Div endings
    processed = processed.replace(/<p[^>]*>/gi, ''); // Remove opening p tags
    processed = processed.replace(/<\/p>/gi, '\n'); // Closing p tags to newline

    // Remove remaining HTML tags
    processed = processed.replace(/<[^>]+>/g, '');

    // Decode HTML entities
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = processed;
    let text = tempDiv.textContent || tempDiv.innerText || '';

    // Clean up excessive whitespace while preserving intentional line breaks
    text = text.replace(/\n{3,}/g, '\n\n'); // Max 2 consecutive newlines
    text = text.trim();

    return text;
  };

  const handleSave = () => {
    if (!editor) return;

    const htmlContent = editor.getHTML();

    // Convert HTML to text content while preserving line breaks
    const textContent = htmlToPlainText(htmlContent);

    // Extract wikilinks and hashtags
    const wikilinkMatches = htmlContent.matchAll(/data-wikilink-title="([^"]+)"/g);
    const wikilinks = [...wikilinkMatches].map(match => match[1]);

    const hashtagMatches = htmlContent.matchAll(/data-hashtag="([^"]+)"/g);
    const tags = [...hashtagMatches].map(match => match[1]);

    onSave({
      title,
      content: textContent,
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
    return (
      <div className="ng-block-editor ng-block-editor-loading">
        <div className="loading-pulse"></div>
        <p>Initializing editor...</p>
      </div>
    );
  }

  return (
    <div className="ng-block-editor">
      {/* Header Toolbar */}
      <div className="ng-block-editor-toolbar">
        <input
          type="text"
          className="ng-block-editor-title"
          value={title}
          onChange={(e) => {
            setTitle(e.target.value);
            setHasChanges(true);
          }}
          placeholder="Untitled"
        />

        <div className="ng-block-editor-actions">
          <button
            onClick={() => setIsPreview(!isPreview)}
            className="ng-btn ng-btn-icon"
            title={isPreview ? 'Edit mode' : 'Preview mode'}
          >
            {isPreview ? <Eye size={18} /> : <EyeOff size={18} />}
          </button>
          <button
            onClick={handleSave}
            className="ng-btn ng-btn-primary"
            disabled={!hasChanges}
          >
            <Save size={16} />
            Save
          </button>
          <button
            onClick={handleCancel}
            className="ng-btn ng-btn-ghost"
          >
            <X size={16} />
            Cancel
          </button>
        </div>
      </div>

      {/* Format Toolbar */}
      <div className="ng-block-editor-format">
        <button
          onClick={() => editor.chain().focus().toggleBold().run()}
          className={`ng-format-btn ${editor.isActive('bold') ? 'active' : ''}`}
          title="Bold (Ctrl+B)"
        >
          <strong>B</strong>
        </button>
        <button
          onClick={() => editor.chain().focus().toggleItalic().run()}
          className={`ng-format-btn ${editor.isActive('italic') ? 'active' : ''}`}
          title="Italic (Ctrl+I)"
        >
          <em>I</em>
        </button>
        <span className="ng-format-divider" />
        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
          className={`ng-format-btn ${editor.isActive('heading', { level: 1 }) ? 'active' : ''}`}
          title="Heading 1"
        >
          H1
        </button>
        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          className={`ng-format-btn ${editor.isActive('heading', { level: 2 }) ? 'active' : ''}`}
          title="Heading 2"
        >
          H2
        </button>
        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
          className={`ng-format-btn ${editor.isActive('heading', { level: 3 }) ? 'active' : ''}`}
          title="Heading 3"
        >
          H3
        </button>
        <span className="ng-format-divider" />
        <button
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          className={`ng-format-btn ${editor.isActive('bulletList') ? 'active' : ''}`}
          title="Bullet List"
        >
          •
        </button>
        <button
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          className={`ng-format-btn ${editor.isActive('orderedList') ? 'active' : ''}`}
          title="Numbered List"
        >
          1.
        </button>
        <button
          onClick={() => editor.chain().focus().toggleTaskList().run()}
          className={`ng-format-btn ${editor.isActive('taskList') ? 'active' : ''}`}
          title="Task List"
        >
          ☑
        </button>
        <span className="ng-format-divider" />
        <button
          onClick={() => editor.chain().focus().toggleBlockquote().run()}
          className={`ng-format-btn ${editor.isActive('blockquote') ? 'active' : ''}`}
          title="Quote"
        >
          "
        </button>
        <button
          onClick={() => editor.chain().focus().toggleCodeBlock().run()}
          className={`ng-format-btn ${editor.isActive('codeBlock') ? 'active' : ''}`}
          title="Code Block"
        >
          {'</>'}
        </button>
      </div>

      {/* Editor Content */}
      <div className="ng-block-editor-body">
        <EditorContent editor={editor} className="ng-block-editor-wrapper" />
      </div>

      {/* Footer */}
      <div className="ng-block-editor-footer">
        <span className="ng-block-editor-hint">
          <kbd>/</kbd> commands
          <kbd>[[</kbd> link note
          <kbd>#</kbd> tag
        </span>
        {hasChanges && (
          <span className="ng-block-editor-unsaved">Unsaved changes</span>
        )}
      </div>
    </div>
  );
}

export default BlockEditor;
