import { Extension } from '@tiptap/core';
import Suggestion from '@tiptap/suggestion';

/**
 * SlashCommandExtension - Triggers command menu on "/" input
 * Uses @tiptap/suggestion utility to handle autocomplete-like behavior
 */
export const SlashCommandExtension = Extension.create({
  name: 'slashCommand',

  addOptions() {
    return {
      suggestion: {
        char: '/',
        startOfLine: false,
        command: ({ editor, range, props }) => {
          props.command({ editor, range });
        },
        items: () => [],
        render: () => ({}),
      },
    };
  },

  addProseMirrorPlugins() {
    return [
      Suggestion({
        editor: this.editor,
        char: this.options.suggestion.char,
        startOfLine: this.options.suggestion.startOfLine,
        command: this.options.suggestion.command,
        items: this.options.suggestion.items,
        render: this.options.suggestion.render,
      }),
    ];
  },
});

/**
 * Default slash command items
 * Each item defines a command with icon, label, description, and action
 */
export const defaultSlashCommands = [
  {
    title: 'Heading 1',
    description: 'Large section heading',
    icon: 'heading1',
    command: ({ editor, range }) => {
      editor
        .chain()
        .focus()
        .deleteRange(range)
        .setNode('heading', { level: 1 })
        .run();
    },
  },
  {
    title: 'Heading 2',
    description: 'Medium section heading',
    icon: 'heading2',
    command: ({ editor, range }) => {
      editor
        .chain()
        .focus()
        .deleteRange(range)
        .setNode('heading', { level: 2 })
        .run();
    },
  },
  {
    title: 'Heading 3',
    description: 'Small section heading',
    icon: 'heading3',
    command: ({ editor, range }) => {
      editor
        .chain()
        .focus()
        .deleteRange(range)
        .setNode('heading', { level: 3 })
        .run();
    },
  },
  {
    title: 'Bullet List',
    description: 'Create a bulleted list',
    icon: 'list',
    command: ({ editor, range }) => {
      editor
        .chain()
        .focus()
        .deleteRange(range)
        .toggleBulletList()
        .run();
    },
  },
  {
    title: 'Numbered List',
    description: 'Create a numbered list',
    icon: 'listOrdered',
    command: ({ editor, range }) => {
      editor
        .chain()
        .focus()
        .deleteRange(range)
        .toggleOrderedList()
        .run();
    },
  },
  {
    title: 'Task List',
    description: 'Create a task list with checkboxes',
    icon: 'checkSquare',
    command: ({ editor, range }) => {
      editor
        .chain()
        .focus()
        .deleteRange(range)
        .toggleTaskList()
        .run();
    },
  },
  {
    title: 'Quote',
    description: 'Create a blockquote',
    icon: 'quote',
    command: ({ editor, range }) => {
      editor
        .chain()
        .focus()
        .deleteRange(range)
        .toggleBlockquote()
        .run();
    },
  },
  {
    title: 'Code Block',
    description: 'Add a code block',
    icon: 'code',
    command: ({ editor, range }) => {
      editor
        .chain()
        .focus()
        .deleteRange(range)
        .toggleCodeBlock()
        .run();
    },
  },
  {
    title: 'Divider',
    description: 'Insert a horizontal rule',
    icon: 'minus',
    command: ({ editor, range }) => {
      editor
        .chain()
        .focus()
        .deleteRange(range)
        .setHorizontalRule()
        .run();
    },
  },
];

export default SlashCommandExtension;
