import { Node, mergeAttributes } from '@tiptap/core';
import { Plugin, PluginKey } from '@tiptap/pm/state';

/**
 * WikilinkExtension - Custom Tiptap node for [[Note Title]] syntax
 * Renders as blue clickable chips
 */
export const WikilinkExtension = Node.create({
  name: 'wikilink',

  group: 'inline',
  inline: true,
  atom: true,

  addAttributes() {
    return {
      title: {
        default: null,
        parseHTML: element => element.getAttribute('data-wikilink-title'),
        renderHTML: attributes => {
          if (!attributes.title) {
            return {};
          }
          return {
            'data-wikilink-title': attributes.title,
          };
        },
      },
      alias: {
        default: null,
        parseHTML: element => element.getAttribute('data-wikilink-alias'),
        renderHTML: attributes => {
          if (!attributes.alias) {
            return {};
          }
          return {
            'data-wikilink-alias': attributes.alias,
          };
        },
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-wikilink-title]',
      },
    ];
  },

  renderHTML({ node, HTMLAttributes }) {
    const displayText = node.attrs.alias || node.attrs.title;
    return [
      'span',
      mergeAttributes(HTMLAttributes, {
        'data-wikilink-title': node.attrs.title,
        'data-wikilink-alias': node.attrs.alias,
        class: 'wikilink-chip',
        contenteditable: 'false',
      }),
      `[[${displayText}]]`,
    ];
  },

  renderText({ node }) {
    const displayText = node.attrs.alias || node.attrs.title;
    return `[[${displayText}]]`;
  },

  addProseMirrorPlugins() {
    return [
      new Plugin({
        key: new PluginKey('wikilink-click-handler'),
        props: {
          handleClick(view, pos, event) {
            const { schema, doc, tr } = view.state;
            const clickedNode = doc.nodeAt(pos);

            if (clickedNode && clickedNode.type.name === 'wikilink') {
              const title = clickedNode.attrs.title;

              // Emit custom event for parent component to handle navigation
              const wikilinkEvent = new CustomEvent('wikilink-click', {
                detail: { title },
                bubbles: true,
              });
              event.target.dispatchEvent(wikilinkEvent);

              return true;
            }

            return false;
          },
        },
      }),
    ];
  },
});
