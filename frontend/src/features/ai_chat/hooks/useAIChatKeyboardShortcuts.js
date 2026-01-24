/**
 * useAIChatKeyboardShortcuts - Keyboard shortcuts for AI Chat
 *
 * Shortcuts:
 * - Ctrl/Cmd + N: New conversation
 * - Ctrl/Cmd + /: Focus input
 * - Ctrl/Cmd + K: Focus search (conversation search)
 * - Escape: Close preview panel / blur input
 */

import { useEffect, useCallback } from 'react';

/**
 * Hook for AI Chat keyboard shortcuts
 *
 * @param {Object} options
 * @param {Function} options.onNewChat - Handler for new chat
 * @param {Function} options.onFocusInput - Handler to focus chat input
 * @param {Function} options.onFocusSearch - Handler to focus conversation search
 * @param {Function} options.onClearPreview - Handler to clear preview panel
 * @param {boolean} options.enabled - Whether shortcuts are enabled
 */
export function useAIChatKeyboardShortcuts({
  onNewChat,
  onFocusInput,
  onFocusSearch,
  onClearPreview,
  enabled = true,
}) {
  const handleKeyDown = useCallback((event) => {
    if (!enabled) return;

    // Check for modifier key (Cmd on Mac, Ctrl on Windows/Linux)
    const isMod = event.metaKey || event.ctrlKey;

    // Ignore if typing in an input/textarea (except for specific shortcuts)
    const isTyping = ['INPUT', 'TEXTAREA'].includes(event.target.tagName) &&
                     event.target.type !== 'checkbox';

    // Ctrl/Cmd + N: New conversation
    if (isMod && event.key === 'n') {
      event.preventDefault();
      onNewChat?.();
      return;
    }

    // Ctrl/Cmd + /: Focus input
    if (isMod && event.key === '/') {
      event.preventDefault();
      onFocusInput?.();
      return;
    }

    // Ctrl/Cmd + K: Focus search
    if (isMod && event.key === 'k') {
      event.preventDefault();
      onFocusSearch?.();
      return;
    }

    // Escape: Close preview / blur input
    if (event.key === 'Escape') {
      // If in an input, blur it
      if (isTyping) {
        event.target.blur();
      }
      // Clear the preview panel
      onClearPreview?.();
      return;
    }
  }, [enabled, onNewChat, onFocusInput, onFocusSearch, onClearPreview]);

  useEffect(() => {
    if (!enabled) return;

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [enabled, handleKeyDown]);
}

export default useAIChatKeyboardShortcuts;
