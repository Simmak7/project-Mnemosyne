import { useCallback } from 'react';
import { api } from '../../../utils/api';
import { useJournalContext } from './JournalContext';

/**
 * useJournalEditor - Manages edit mode and save for the journal day view.
 */
export function useJournalEditor() {
  const { dailyNote, isEditing, setIsEditing, refetch } = useJournalContext();

  const handleSave = useCallback(async (data) => {
    if (!dailyNote?.id) return;

    await api.put(`/notes/${dailyNote.id}`, {
      title: dailyNote.title,
      content: data.content || dailyNote.content,
      html_content: data.html_content || null,
    });

    setIsEditing(false);
    refetch();
  }, [dailyNote, setIsEditing, refetch]);

  const handleCancel = useCallback(() => {
    setIsEditing(false);
  }, [setIsEditing]);

  const toggleEdit = useCallback(() => {
    setIsEditing(prev => !prev);
  }, [setIsEditing]);

  return {
    isEditing,
    toggleEdit,
    handleSave,
    handleCancel,
  };
}

export default useJournalEditor;
