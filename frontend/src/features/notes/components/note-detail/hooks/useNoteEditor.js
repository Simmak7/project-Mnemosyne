import { useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { api } from '../../../../../utils/api';

/**
 * Hook for note editing functionality
 */
export function useNoteEditor({ note, setNote, selectNote }) {
  const [isEditing, setIsEditing] = useState(false);
  const queryClient = useQueryClient();

  // Handle edit start
  const handleEditStart = useCallback(() => {
    setIsEditing(true);
  }, []);

  // Handle save from editor
  const handleSave = useCallback(async (editData) => {
    if (!note) return;

    try {
      const updatedNote = await api.put(`/notes/${note.id}`, {
        title: editData.title,
        content: editData.content,
        html_content: editData.html
      });

      setNote(prev => ({
        ...prev,
        title: updatedNote.title,
        content: updatedNote.content,
        html_content: updatedNote.html_content,
        updated_at: updatedNote.updated_at
      }));
      setIsEditing(false);
      queryClient.invalidateQueries({ queryKey: ['notes-enhanced'] });
    } catch (err) {
      console.error('Error saving note:', err);
    }
  }, [note, setNote, queryClient]);

  // Handle cancel editing
  const handleCancelEdit = useCallback(() => {
    setIsEditing(false);
  }, []);

  // Handle wikilink navigation
  const handleWikilinkClick = useCallback(async (title) => {
    try {
      const notes = await api.get(`/notes/?search=${encodeURIComponent(title)}`);
      const target = notes.find(n =>
        n.title?.toLowerCase() === title.toLowerCase() ||
        n.slug === title.toLowerCase().replace(/\s+/g, '-')
      );
      if (target) {
        selectNote(target.id);
      }
    } catch (err) {
      console.error('Error navigating to wikilink:', err);
    }
  }, [selectNote]);

  // Handle tag click
  const handleTagClick = useCallback((tagName) => {
    console.log('Tag clicked:', tagName);
  }, []);

  return {
    isEditing,
    handleEditStart,
    handleSave,
    handleCancelEdit,
    handleWikilinkClick,
    handleTagClick,
  };
}
