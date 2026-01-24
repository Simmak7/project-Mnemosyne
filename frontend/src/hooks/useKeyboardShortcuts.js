import { useEffect } from 'react';

/**
 * Custom hook for registering keyboard shortcuts
 * @param {Object} shortcuts - Map of key combinations to handlers
 * Example: { 'cmd+k': () => openSearch(), 'cmd+n': () => newNote() }
 */
function useKeyboardShortcuts(shortcuts) {
  useEffect(() => {
    const handleKeyDown = (event) => {
      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const cmdOrCtrl = isMac ? event.metaKey : event.ctrlKey;

      // Build key combination string
      let combo = '';
      if (cmdOrCtrl) combo += 'cmd+';
      if (event.shiftKey) combo += 'shift+';
      if (event.altKey) combo += 'alt+';
      combo += event.key.toLowerCase();

      // Check if this combination has a handler
      const handler = shortcuts[combo];
      if (handler) {
        event.preventDefault();
        handler(event);
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [shortcuts]);
}

export default useKeyboardShortcuts;
