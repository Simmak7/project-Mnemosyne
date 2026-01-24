import { Node, mergeAttributes } from '@tiptap/core';
import { Plugin, PluginKey } from '@tiptap/pm/state';

/**
 * HashtagExtension - Custom Tiptap node for #tag syntax
 * Renders as orange chips
 */
export const HashtagExtension = Node.create({
  name: 'hashtag',

  group: 'inline',
  inline: true,
  atom: true,

  addAttributes() {
    return {
      tag: {
        default: null,
        parseHTML: element => element.getAttribute('data-hashtag'),
        renderHTML: attributes => {
          if (!attributes.tag) {
            return {};
          }
          return {
            'data-hashtag': attributes.tag,
          };
        },
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-hashtag]',
      },
    ];
  },

  renderHTML({ node, HTMLAttributes }) {
    return [
      'span',
      mergeAttributes(HTMLAttributes, {
        'data-hashtag': node.attrs.tag,
        class: 'hashtag-chip',
        contenteditable: 'false',
      }),
      `#${node.attrs.tag}`,
    ];
  },

  renderText({ node }) {
    return `#${node.attrs.tag}`;
  },

  addProseMirrorPlugins() {
    return [
      new Plugin({
        key: new PluginKey('hashtag-click-handler'),
        props: {
          handleClick(view, pos, event) {
            const { schema, doc, tr } = view.state;
            const clickedNode = doc.nodeAt(pos);

            if (clickedNode && clickedNode.type.name === 'hashtag') {
              const tag = clickedNode.attrs.tag;

              // Emit custom event for parent component to handle tag filtering
              const hashtagEvent = new CustomEvent('hashtag-click', {
                detail: { tag },
                bubbles: true,
              });
              event.target.dispatchEvent(hashtagEvent);

              return true;
            }

            return false;
          },
        },
      }),
    ];
  },
});
