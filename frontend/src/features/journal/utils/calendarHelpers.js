import {
  startOfMonth, endOfMonth, startOfWeek, endOfWeek,
  eachDayOfInterval, format, addMonths, subMonths,
  isSameDay, isSameMonth, isToday as isTodayFn
} from 'date-fns';

/**
 * Generate the 42-cell grid (6 weeks) for a month view.
 * @param {number} year
 * @param {number} month - 1-indexed
 * @returns {Date[]} Array of 42 dates
 */
export function getMonthGrid(year, month) {
  const monthStart = startOfMonth(new Date(year, month - 1));
  const monthEnd = endOfMonth(monthStart);
  const gridStart = startOfWeek(monthStart, { weekStartsOn: 0 });
  const gridEnd = endOfWeek(monthEnd, { weekStartsOn: 0 });
  return eachDayOfInterval({ start: gridStart, end: gridEnd });
}

/**
 * Parse "YYYY-MM" string into { year, month }.
 */
export function parseCalendarMonth(monthStr) {
  const [y, m] = monthStr.split('-').map(Number);
  return { year: y, month: m };
}

/**
 * Navigate month forward/backward.
 * @param {string} monthStr - "YYYY-MM"
 * @param {number} direction - 1 (next) or -1 (prev)
 * @returns {string} "YYYY-MM"
 */
export function navigateMonth(monthStr, direction) {
  const { year, month } = parseCalendarMonth(monthStr);
  const base = new Date(year, month - 1);
  const next = direction > 0 ? addMonths(base, 1) : subMonths(base, 1);
  return format(next, 'yyyy-MM');
}

export { format, isSameDay, isSameMonth, isTodayFn as isToday };
