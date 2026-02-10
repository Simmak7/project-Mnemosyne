import { useState, useEffect, useCallback } from 'react';
import { api } from '../../../utils/api';

/**
 * useJournalEntries - Fetches recent daily notes for the entry list.
 *
 * @param {number} days - How many days back to look
 * @returns {{ entries: Array, isLoading: boolean, refetch: Function }}
 */
export function useJournalEntries(days = 30) {
  const [entries, setEntries] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchEntries = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await api.get(`/buckets/daily?days=${days}`);
      // Sort by date descending (newest first)
      const sorted = (data.notes || []).sort((a, b) => {
        if (!a.date || !b.date) return 0;
        return b.date.localeCompare(a.date);
      });
      setEntries(sorted);
    } catch (err) {
      console.error('Failed to fetch journal entries:', err);
      setEntries([]);
    } finally {
      setIsLoading(false);
    }
  }, [days]);

  useEffect(() => {
    fetchEntries();
  }, [fetchEntries]);

  return { entries, isLoading, refetch: fetchEntries };
}

export default useJournalEntries;
