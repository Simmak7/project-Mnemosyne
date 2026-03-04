import React, { useState, useEffect, useCallback, useRef } from 'react';

/**
 * FloatingFormatToolbar - Appears above text selection on mobile.
 * Shows essential formatting buttons: Bold, Italic, H1, H2, List, Quote.
 */
function FloatingFormatToolbar({ editor }) {
  const [visible, setVisible] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const toolbarRef = useRef(null);

  const updatePosition = useCallback(() => {
    if (!editor) return;

    const { from, to, empty } = editor.state.selection;
    if (empty) {
      setVisible(false);
      return;
    }

    // Get selection coordinates from the editor view
    const start = editor.view.coordsAtPos(from);
    const end = editor.view.coordsAtPos(to);

    const toolbarWidth = 280;
    const toolbarHeight = 44;
    const centerX = (start.left + end.right) / 2;
    let left = centerX - toolbarWidth / 2;
    const top = start.top - toolbarHeight - 8;

    // Keep within viewport
    const vpWidth = window.visualViewport?.width ?? window.innerWidth;
    left = Math.max(8, Math.min(left, vpWidth - toolbarWidth - 8));
    const safeTop = top < 8 ? end.bottom + 8 : top;

    setPosition({ top: safeTop, left });
    setVisible(true);
  }, [editor]);

  useEffect(() => {
    if (!editor) return;

    const onSelectionUpdate = () => {
      // Small delay to let the selection settle
      requestAnimationFrame(updatePosition);
    };

    editor.on('selectionUpdate', onSelectionUpdate);
    editor.on('blur', () => setVisible(false));

    return () => {
      editor.off('selectionUpdate', onSelectionUpdate);
      editor.off('blur', () => setVisible(false));
    };
  }, [editor, updatePosition]);

  if (!visible || !editor) return null;

  const btn = (action, label, isActive) => (
    <button
      className={`ng-float-fmt-btn ${isActive ? 'active' : ''}`}
      onPointerDown={(e) => {
        e.preventDefault(); // Prevent losing selection
        action();
      }}
    >
      {label}
    </button>
  );

  return (
    <div
      ref={toolbarRef}
      className="ng-floating-format-toolbar"
      style={{ top: `${position.top}px`, left: `${position.left}px` }}
    >
      {btn(() => editor.chain().focus().toggleBold().run(), <strong>B</strong>, editor.isActive('bold'))}
      {btn(() => editor.chain().focus().toggleItalic().run(), <em>I</em>, editor.isActive('italic'))}
      <span className="ng-float-fmt-divider" />
      {btn(() => editor.chain().focus().toggleHeading({ level: 1 }).run(), 'H1', editor.isActive('heading', { level: 1 }))}
      {btn(() => editor.chain().focus().toggleHeading({ level: 2 }).run(), 'H2', editor.isActive('heading', { level: 2 }))}
      <span className="ng-float-fmt-divider" />
      {btn(() => editor.chain().focus().toggleBulletList().run(), '\u2022', editor.isActive('bulletList'))}
      {btn(() => editor.chain().focus().toggleBlockquote().run(), '\u201C', editor.isActive('blockquote'))}
    </div>
  );
}

export default FloatingFormatToolbar;
