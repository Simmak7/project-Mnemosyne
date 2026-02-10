import React from 'react';

/**
 * Format toolbar with text formatting buttons
 */
function FormatToolbar({ editor }) {
  if (!editor) return null;

  return (
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
  );
}

export default FormatToolbar;
