import { useCallback, useRef, useState, useEffect } from 'react';
import { ReactRenderer } from '@tiptap/react';
import tippy from 'tippy.js';
import SlashCommandMenu from '../components/SlashCommandMenu';
import { defaultSlashCommands } from '../extensions/SlashCommandExtension';

/**
 * useSlashCommands - Hook providing slash command suggestion configuration
 * Returns a suggestion object compatible with @tiptap/suggestion
 *
 * @param {Array} customCommands - Optional custom commands to add/override defaults
 * @returns {Object} Suggestion configuration for SlashCommandExtension
 */
export function useSlashCommands(customCommands = []) {
  const [commands] = useState(() => {
    // Merge custom commands with defaults, custom takes precedence
    const customTitles = new Set(customCommands.map(c => c.title));
    const defaults = defaultSlashCommands.filter(c => !customTitles.has(c.title));
    return [...customCommands, ...defaults];
  });

  const componentRef = useRef(null);
  const popupRef = useRef(null);

  // Create suggestion configuration
  const suggestion = {
    items: ({ query }) => {
      const searchQuery = query.toLowerCase();
      return commands.filter(item =>
        item.title.toLowerCase().includes(searchQuery) ||
        item.description.toLowerCase().includes(searchQuery)
      ).slice(0, 10);
    },

    render: () => {
      return {
        onStart: (props) => {
          componentRef.current = new ReactRenderer(SlashCommandMenu, {
            props,
            editor: props.editor,
          });

          if (!props.clientRect) return;

          popupRef.current = tippy('body', {
            getReferenceClientRect: props.clientRect,
            appendTo: () => document.body,
            content: componentRef.current.element,
            showOnCreate: true,
            interactive: true,
            trigger: 'manual',
            placement: 'bottom-start',
            animation: false,
            offset: [0, 8],
          })[0];
        },

        onUpdate: (props) => {
          componentRef.current?.updateProps(props);

          if (!props.clientRect) return;

          popupRef.current?.setProps({
            getReferenceClientRect: props.clientRect,
          });
        },

        onKeyDown: (props) => {
          if (props.event.key === 'Escape') {
            popupRef.current?.hide();
            return true;
          }

          return componentRef.current?.ref?.onKeyDown(props) || false;
        },

        onExit: () => {
          popupRef.current?.destroy();
          componentRef.current?.destroy();
        },
      };
    },
  };

  return { suggestion, commands };
}

/**
 * Creates a configured SlashCommandExtension with the provided commands
 * @param {Object} SlashCommandExtension - The extension to configure
 * @param {Array} customCommands - Optional custom commands
 * @returns {Object} Configured extension
 */
export function configureSlashCommands(SlashCommandExtension, customCommands = []) {
  const commands = [
    ...customCommands,
    ...defaultSlashCommands.filter(c =>
      !customCommands.some(cc => cc.title === c.title)
    ),
  ];

  let componentRef = null;
  let popupRef = null;

  return SlashCommandExtension.configure({
    suggestion: {
      items: ({ query }) => {
        const searchQuery = query.toLowerCase();
        return commands.filter(item =>
          item.title.toLowerCase().includes(searchQuery) ||
          item.description.toLowerCase().includes(searchQuery)
        ).slice(0, 10);
      },

      render: () => {
        return {
          onStart: (props) => {
            componentRef = new ReactRenderer(SlashCommandMenu, {
              props,
              editor: props.editor,
            });

            if (!props.clientRect) return;

            popupRef = tippy('body', {
              getReferenceClientRect: props.clientRect,
              appendTo: () => document.body,
              content: componentRef.element,
              showOnCreate: true,
              interactive: true,
              trigger: 'manual',
              placement: 'bottom-start',
              animation: false,
              offset: [0, 8],
            })[0];
          },

          onUpdate: (props) => {
            componentRef?.updateProps(props);

            if (!props.clientRect) return;

            popupRef?.setProps({
              getReferenceClientRect: props.clientRect,
            });
          },

          onKeyDown: (props) => {
            if (props.event.key === 'Escape') {
              popupRef?.hide();
              return true;
            }

            return componentRef?.ref?.onKeyDown(props) || false;
          },

          onExit: () => {
            popupRef?.destroy();
            componentRef?.destroy();
          },
        };
      },
    },
  });
}

export default useSlashCommands;
