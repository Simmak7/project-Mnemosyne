import { useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { api } from '../../../../../utils/api';

/**
 * Hook for note action handlers
 */
export function useNoteActions({
  note,
  setNote,
  selectedNoteId,
  selectNote,
  refreshCounts,
}) {
  const queryClient = useQueryClient();

  // Refresh current note data
  const handleRefreshNote = useCallback(async () => {
    if (!selectedNoteId) return;

    try {
      const data = await api.get(`/notes/${selectedNoteId}/enhanced`);
      setNote(data);
    } catch (err) {
      console.error('Error refreshing note:', err);
    }
  }, [selectedNoteId, setNote]);

  // Handle favorite toggle
  const handleToggleFavorite = useCallback(async () => {
    if (!note) return;

    try {
      const updatedNote = await api.post(`/notes/${note.id}/favorite`);
      setNote(prev => ({ ...prev, is_favorite: updatedNote.is_favorite }));
      queryClient.invalidateQueries({ queryKey: ['notes-enhanced'] });
      refreshCounts();
    } catch (err) {
      console.error('Error toggling favorite:', err);
    }
  }, [note, setNote, queryClient, refreshCounts]);

  // Handle move to trash
  const handleMoveToTrash = useCallback(async () => {
    if (!note) return;

    if (!window.confirm('Move this note to trash?')) return;

    // Immediately clear the detail panel (optimistic)
    const noteId = note.id;
    setNote(null);
    selectNote(null);

    // Optimistically remove from cached notes list so it disappears immediately
    queryClient.setQueryData(['notes-enhanced'], (old) => {
      if (!old) return old;
      return old.filter(n => n.id !== noteId);
    });

    try {
      await api.post(`/notes/${noteId}/trash`);
      queryClient.invalidateQueries({ queryKey: ['notes-enhanced'] });
      queryClient.invalidateQueries({ queryKey: ['notes-trash'] });
      refreshCounts();
    } catch (err) {
      console.error('Error moving note to trash:', err);
      // Refetch to restore the note if the API call failed
      queryClient.invalidateQueries({ queryKey: ['notes-enhanced'] });
    }
  }, [note, setNote, selectNote, queryClient, refreshCounts]);

  // Handle toggle reviewed
  const handleToggleReviewed = useCallback(async () => {
    if (!note) return;

    try {
      const updatedNote = await api.post(`/notes/${note.id}/reviewed`);
      setNote(prev => ({ ...prev, is_reviewed: updatedNote.is_reviewed }));
      queryClient.invalidateQueries({ queryKey: ['notes-enhanced'] });
      refreshCounts();
    } catch (err) {
      console.error('Error toggling reviewed:', err);
    }
  }, [note, setNote, queryClient, refreshCounts]);

  // Handle restore from trash
  const handleRestoreFromTrash = useCallback(async () => {
    if (!note) return;

    const noteId = note.id;
    setNote(null);
    selectNote(null);

    // Optimistically remove from trash list so it disappears immediately
    queryClient.setQueryData(['notes-trash'], (old) => {
      if (!old) return old;
      return old.filter(n => n.id !== noteId);
    });

    try {
      await api.post(`/notes/${noteId}/restore`);
      queryClient.invalidateQueries({ queryKey: ['notes-enhanced'] });
      queryClient.invalidateQueries({ queryKey: ['notes-trash'] });
      refreshCounts();
    } catch (err) {
      console.error('Error restoring note from trash:', err);
      queryClient.invalidateQueries({ queryKey: ['notes-trash'] });
    }
  }, [note, setNote, selectNote, queryClient, refreshCounts]);

  return {
    handleRefreshNote,
    handleToggleFavorite,
    handleMoveToTrash,
    handleToggleReviewed,
    handleRestoreFromTrash,
  };
}
