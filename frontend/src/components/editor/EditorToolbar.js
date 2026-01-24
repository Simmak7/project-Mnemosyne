import React from 'react';
import {
  FiBold,
  FiItalic,
  FiCode,
  FiLink,
  FiImage,
  FiList,
  FiCheckSquare,
  FiAlignLeft,
  FiMinusSquare,
} from 'react-icons/fi';
import './EditorToolbar.css';

/**
 * Markdown editor toolbar with formatting buttons
 *
 * Features:
 * - Bold, italic, code formatting
 * - Links and images
 * - Lists (ordered, unordered, checkboxes)
 * - Headings
 * - Horizontal rules
 * - Keyboard shortcuts displayed
 */
function EditorToolbar({ onInsert, onFormat }) {
  const toolbarActions = [
    {
      id: 'bold',
      label: 'Bold',
      icon: <FiBold />,
      action: () => onFormat('**'),
      shortcut: 'Ctrl+B',
    },
    {
      id: 'italic',
      label: 'Italic',
      icon: <FiItalic />,
      action: () => onFormat('*'),
      shortcut: 'Ctrl+I',
    },
    {
      id: 'code',
      label: 'Inline Code',
      icon: <FiCode />,
      action: () => onFormat('`'),
      shortcut: 'Ctrl+`',
    },
    {
      id: 'divider-1',
      type: 'divider',
    },
    {
      id: 'link',
      label: 'Insert Link',
      icon: <FiLink />,
      action: () => onInsert('[link text](https://example.com)'),
      shortcut: 'Ctrl+K',
    },
    {
      id: 'image',
      label: 'Insert Image',
      icon: <FiImage />,
      action: () => onInsert('![alt text](image-url.jpg)'),
      shortcut: 'Ctrl+Shift+I',
    },
    {
      id: 'divider-2',
      type: 'divider',
    },
    {
      id: 'heading',
      label: 'Heading',
      icon: <FiAlignLeft />,
      action: () => onInsert('\n## Heading\n'),
      shortcut: 'Ctrl+H',
    },
    {
      id: 'ul',
      label: 'Unordered List',
      icon: <FiList />,
      action: () => onInsert('\n- Item 1\n- Item 2\n- Item 3\n'),
      shortcut: 'Ctrl+U',
    },
    {
      id: 'ol',
      label: 'Ordered List',
      icon: <FiList />,
      action: () => onInsert('\n1. Item 1\n2. Item 2\n3. Item 3\n'),
      shortcut: 'Ctrl+O',
    },
    {
      id: 'checkbox',
      label: 'Checkbox List',
      icon: <FiCheckSquare />,
      action: () => onInsert('\n- [ ] Todo item\n- [x] Completed item\n'),
      shortcut: 'Ctrl+Shift+C',
    },
    {
      id: 'divider-3',
      type: 'divider',
    },
    {
      id: 'hr',
      label: 'Horizontal Rule',
      icon: <FiMinusSquare />,
      action: () => onInsert('\n---\n'),
      shortcut: 'Ctrl+Shift+H',
    },
  ];

  return (
    <div className="editor-toolbar">
      {toolbarActions.map((action) => {
        if (action.type === 'divider') {
          return <div key={action.id} className="toolbar-divider" />;
        }

        return (
          <button
            key={action.id}
            className="toolbar-button"
            onClick={action.action}
            title={`${action.label}${action.shortcut ? ` (${action.shortcut})` : ''}`}
            aria-label={action.label}
          >
            {action.icon}
          </button>
        );
      })}

      <div className="toolbar-spacer" />

      <div className="toolbar-help">
        <span className="toolbar-help-text">
          💡 Use Markdown syntax for formatting
        </span>
      </div>
    </div>
  );
}

export default EditorToolbar;
