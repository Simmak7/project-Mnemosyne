import React, { createContext, useContext, useCallback } from 'react';
import { format } from 'date-fns';
import { usePersistedState } from '../../../hooks/usePersistedState';
import { useDailyNote } from '../../daily/hooks/useDailyNote';
import { useJournalEntries } from './useJournalEntries';

const JournalContext = createContext(null);

export function JournalProvider({ children }) {
  const [selectedDate, setSelectedDate] = usePersistedState(
    'journal:selectedDate',
    format(new Date(), 'yyyy-MM-dd')
  );
  const [calendarMonth, setCalendarMonth] = usePersistedState(
    'journal:calendarMonth',
    format(new Date(), 'yyyy-MM')
  );
  const [isEditing, setIsEditing] = usePersistedState('journal:isEditing', false);

  // Parse selected date for the daily note hook
  const selectedDateObj = (() => {
    try {
      const [y, m, d] = selectedDate.split('-').map(Number);
      return new Date(y, m - 1, d);
    } catch {
      return new Date();
    }
  })();

  const {
    dailyNote,
    isLoading,
    error,
    refetch,
    appendContent: rawAppendContent,
    updateContent: rawUpdateContent,
    toggleCheckbox: rawToggleCheckbox,
    isToday,
  } = useDailyNote(selectedDateObj);

  // Lift entries into context so sidebar and insights can share them
  const {
    entries,
    isLoading: entriesLoading,
    refetch: refetchEntries,
  } = useJournalEntries(90);

  // Wrap appendContent to also refetch entries after change
  const appendContent = useCallback(async (type, content) => {
    const result = await rawAppendContent(type, content);
    await refetchEntries();
    return result;
  }, [rawAppendContent, refetchEntries]);

  // Wrap updateContent to also refetch entries after change
  const updateContent = useCallback(async (newContent) => {
    const result = await rawUpdateContent(newContent);
    await refetchEntries();
    return result;
  }, [rawUpdateContent, refetchEntries]);

  // Wrap toggleCheckbox to also refetch entries after change
  const toggleCheckbox = useCallback(async (lineIdentifier, checked) => {
    const result = await rawToggleCheckbox(lineIdentifier, checked);
    await refetchEntries();
    return result;
  }, [rawToggleCheckbox, refetchEntries]);

  const selectDate = useCallback((dateStr) => {
    setSelectedDate(dateStr);
  }, [setSelectedDate]);

  const navigateToToday = useCallback(() => {
    const today = format(new Date(), 'yyyy-MM-dd');
    setSelectedDate(today);
    setCalendarMonth(format(new Date(), 'yyyy-MM'));
  }, [setSelectedDate, setCalendarMonth]);

  const value = {
    // Date state
    selectedDate,
    selectDate,
    calendarMonth,
    setCalendarMonth,
    navigateToToday,
    isToday,

    // Daily note
    dailyNote,
    isLoading,
    error,
    refetch,
    appendContent,
    updateContent,
    toggleCheckbox,

    // Entries (shared)
    entries,
    entriesLoading,
    refetchEntries,

    // Editor
    isEditing,
    setIsEditing,
  };

  return (
    <JournalContext.Provider value={value}>
      {children}
    </JournalContext.Provider>
  );
}

export function useJournalContext() {
  const context = useContext(JournalContext);
  if (!context) {
    throw new Error('useJournalContext must be used within a JournalProvider');
  }
  return context;
}

export default JournalContext;
