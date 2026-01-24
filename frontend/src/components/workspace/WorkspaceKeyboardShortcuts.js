import { useEffect } from 'react';
import { useWorkspaceState } from '../../hooks/useWorkspaceState';
import { useSmartBuckets } from '../../hooks/useSmartBuckets';

/**
 * WorkspaceKeyboardShortcuts - Global keyboard shortcuts for workspace
 *
 * Shortcuts:
 * - Ctrl+Shift+D (Cmd+Shift+D on Mac): Create/open today's daily note
 * - Ctrl+\ : Toggle left sidebar
 * - Ctrl+Shift+\ : Toggle right sidebar
 */
function WorkspaceKeyboardShortcuts({ onToggleLeft, onToggleRight }) {
  const { selectNote } = useWorkspaceState();
  const { createTodayNote } = useSmartBuckets();

  useEffect(() => {
    const handleKeyDown = async (event) => {
      // Ctrl+Shift+D (Cmd+Shift+D on Mac) - Create/open today's daily note
      // Use case-insensitive comparison and check both key and code
      const isDKey = event.key?.toLowerCase() === 'd' || event.code === 'KeyD';
      if ((event.ctrlKey || event.metaKey) && event.shiftKey && isDKey) {
        event.preventDefault();
        event.stopPropagation();

        try {
          const dailyNote = await createTodayNote();

          if (dailyNote) {
            // Open the note in the center pane
            selectNote(dailyNote.id);
          }
        } catch (error) {
          // Only log errors in development
          if (process.env.NODE_ENV === 'development') {
            console.error('Failed to create/open daily note:', error);
          }
          alert(`Failed to create daily note: ${error.message}`);
        }
      }

      // Ctrl+\ - Toggle left sidebar
      if ((event.ctrlKey || event.metaKey) && event.key === '\\' && !event.shiftKey) {
        event.preventDefault();
        onToggleLeft?.();
      }

      // Ctrl+Shift+\ - Toggle right sidebar
      if ((event.ctrlKey || event.metaKey) && event.key === '\\' && event.shiftKey) {
        event.preventDefault();
        onToggleRight?.();
      }
    };

    // Add event listener
    window.addEventListener('keydown', handleKeyDown);

    // Cleanup
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [createTodayNote, selectNote, onToggleLeft, onToggleRight]);

  // This component doesn't render anything
  return null;
}

export default WorkspaceKeyboardShortcuts;
