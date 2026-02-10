import { useState, useEffect, useCallback } from 'react';
import { api } from '../../../utils/api';
import { parseCalendarMonth } from '../utils/calendarHelpers';

/**
 * useCalendarData - Fetches lightweight calendar summary for a month.
 * Returns a Map<dateStr, summary> for O(1) lookups per cell.
 *
 * @param {string} calendarMonth - "YYYY-MM"
 * @returns {{ calendarData: Map, isLoading: boolean, refetch: Function }}
 */
export function useCalendarData(calendarMonth) {
  const [calendarData, setCalendarData] = useState(new Map());
  const [isLoading, setIsLoading] = useState(false);

  const fetchCalendar = useCallback(async () => {
    const { year, month } = parseCalendarMonth(calendarMonth);

    setIsLoading(true);
    try {
      const data = await api.get(`/buckets/daily/calendar/${year}/${month}`);
      const map = new Map();
      (data.days || []).forEach(day => {
        map.set(day.date, day);
      });
      setCalendarData(map);
    } catch (err) {
      console.error('Failed to fetch calendar data:', err);
      setCalendarData(new Map());
    } finally {
      setIsLoading(false);
    }
  }, [calendarMonth]);

  useEffect(() => {
    fetchCalendar();
  }, [fetchCalendar]);

  return { calendarData, isLoading, refetch: fetchCalendar };
}

export default useCalendarData;
