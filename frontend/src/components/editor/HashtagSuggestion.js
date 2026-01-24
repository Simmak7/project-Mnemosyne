import Fuse from 'fuse.js';
import { ReactRenderer } from '@tiptap/react';
import tippy from 'tippy.js';
import { SuggestionList } from './SuggestionList';

/**
 * Hashtag autocomplete suggestion configuration
 * Triggers on # and provides fuzzy search dropdown for existing tags
 */
export const hashtagSuggestion = (tags) => ({
  char: '#',

  items: ({ query }) => {
    if (!tags || tags.length === 0) return [];

    // Fuzzy search using Fuse.js
    const fuse = new Fuse(tags, {
      keys: ['name'],
      threshold: 0.3,
      includeScore: true,
    });

    if (!query) {
      return tags.slice(0, 10);
    }

    const results = fuse.search(query);
    return results.map(result => result.item).slice(0, 10);
  },

  render: () => {
    let component;
    let popup;

    return {
      onStart: props => {
        component = new ReactRenderer(SuggestionList, {
          props: { ...props, isHashtag: true },
          editor: props.editor,
        });

        if (!props.clientRect) {
          return;
        }

        popup = tippy('body', {
          getReferenceClientRect: props.clientRect,
          appendTo: () => document.body,
          content: component.element,
          showOnCreate: true,
          interactive: true,
          trigger: 'manual',
          placement: 'bottom-start',
        });
      },

      onUpdate(props) {
        component.updateProps({ ...props, isHashtag: true });

        if (!props.clientRect) {
          return;
        }

        popup[0].setProps({
          getReferenceClientRect: props.clientRect,
        });
      },

      onKeyDown(props) {
        if (props.event.key === 'Escape') {
          popup[0].hide();
          return true;
        }

        return component.ref?.onKeyDown(props);
      },

      onExit() {
        popup[0].destroy();
        component.destroy();
      },
    };
  },

  command: ({ editor, range, props }) => {
    // Delete the # trigger text
    editor.commands.deleteRange(range);

    // Insert hashtag node
    editor
      .chain()
      .focus()
      .insertContent({
        type: 'hashtag',
        attrs: {
          tag: props.name,
        },
      })
      .insertContent(' ')
      .run();
  },

  allow: ({ editor, range }) => {
    return editor.can().insertContentAt(range, { type: 'hashtag' });
  },
});
