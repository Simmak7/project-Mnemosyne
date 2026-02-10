import { useEffect } from 'react';
import { useNoteContext } from './NoteContext';

/**
 * useValidateNoteSelection - Clears persisted selection if the note
 * no longer exists in the fetched list (deleted, trashed, etc.)
 *
 * Skips one validation cycle after external navigation (from Journal,
 * Brain Graph, etc.) to prevent a race condition where the target note
 * isn't yet in the fetched list and would be incorrectly cleared.
 *
 * @param {Array} notes - currently visible notes
 * @param {boolean} isLoading - whether notes are still loading
 */
export function useValidateNoteSelection(notes, isLoading) {
  const { selectedNoteId, selectNote, skipValidation, setSkipValidation } = useNoteContext();

  useEffect(() => {
    if (isLoading || !selectedNoteId || !notes.length) return;

    // After external navigation, skip one validation cycle
    if (skipValidation) {
      setSkipValidation(false);
      return;
    }

    const exists = notes.some(n => n.id === selectedNoteId);
    if (!exists) {
      selectNote(null);
    }
  }, [notes, isLoading, selectedNoteId, selectNote, skipValidation, setSkipValidation]);
}

export default useValidateNoteSelection;
