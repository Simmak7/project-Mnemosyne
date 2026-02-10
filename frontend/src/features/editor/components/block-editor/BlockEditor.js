import React, { useEffect, useState } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import TaskList from '@tiptap/extension-task-list';
import TaskItem from '@tiptap/extension-task-item';
import { Mention } from '@tiptap/extension-mention';
import { WikilinkExtension } from '../../../../extensions/WikilinkExtension';
import { HashtagExtension } from '../../../../extensions/HashtagExtension';
import { SlashCommandExtension } from '../../extensions/SlashCommandExtension';
import { configureSlashCommands } from '../../hooks/useSlashCommands';
import { wikilinkSuggestion } from '../../../../components/editor/WikilinkSuggestion';
import { hashtagSuggestion } from '../../../../components/editor/HashtagSuggestion';
import 'tippy.js/dist/tippy.css';
import '../BlockEditor.css';

import { EditorToolbar, FormatToolbar, EditorFooter, LoadingState } from './components';
import {
  convertWikilinks,
  convertHashtags,
  convertPlainTextToHtml,
  htmlToPlainText,
  getInitialContent,
  extractLinksAndTags,
} from './utils';

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
    content: getInitialContent(note),
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

  const handleSave = () => {
    if (!editor) return;

    const htmlContent = editor.getHTML();
    const textContent = htmlToPlainText(htmlContent);
    const { wikilinks, tags } = extractLinksAndTags(htmlContent);

    onSave({
      title,
      content: textContent,
      html: htmlContent,
      wikilinks,
      tags,
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
    return <LoadingState />;
  }

  return (
    <div className="ng-block-editor">
      <EditorToolbar
        title={title}
        setTitle={setTitle}
        hasChanges={hasChanges}
        setHasChanges={setHasChanges}
        isPreview={isPreview}
        setIsPreview={setIsPreview}
        onSave={handleSave}
        onCancel={handleCancel}
      />

      <FormatToolbar editor={editor} />

      <div className="ng-block-editor-body">
        <EditorContent editor={editor} className="ng-block-editor-wrapper" />
      </div>

      <EditorFooter hasChanges={hasChanges} />
    </div>
  );
}

export default BlockEditor;
