import { useState, useRef, useCallback } from 'react';

const PULL_THRESHOLD = 70;
const MAX_PULL = 120;

/**
 * usePullToRefresh - Touch-based pull-to-refresh for mobile list views.
 *
 * @param {function} onRefresh - Async function to call on refresh (e.g. refetch)
 * @param {object} options - { enabled: true }
 * @returns {{ pullDistance, isRefreshing, handlers }}
 */
export function usePullToRefresh(onRefresh, { enabled = true } = {}) {
  const [pullDistance, setPullDistance] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const touchStart = useRef(null);
  const scrollTop = useRef(0);

  const onTouchStart = useCallback((e) => {
    if (!enabled || isRefreshing) return;
    // Only start pull if scrolled to very top
    const el = e.currentTarget;
    // Check the scroll container: either current element or its first scrollable child
    const scrollEl = el.scrollTop != null ? el : el.firstElementChild;
    scrollTop.current = scrollEl?.scrollTop ?? 0;
    if (scrollTop.current > 2) {
      touchStart.current = null;
      return;
    }
    touchStart.current = e.touches[0].clientY;
  }, [enabled, isRefreshing]);

  const onTouchMove = useCallback((e) => {
    if (!enabled || isRefreshing || touchStart.current === null) return;
    const currentY = e.touches[0].clientY;
    const diff = currentY - touchStart.current;

    if (diff > 0 && scrollTop.current <= 2) {
      // Prevent native scroll while pulling — only if we're at very top
      if (diff > 10) e.preventDefault();
      const distance = Math.min(diff * 0.5, MAX_PULL);
      setPullDistance(distance);
    } else {
      // User is scrolling normally — cancel pull tracking
      touchStart.current = null;
      setPullDistance(0);
    }
  }, [enabled, isRefreshing]);

  const onTouchEnd = useCallback(async () => {
    if (!enabled || touchStart.current === null) return;
    touchStart.current = null;

    if (pullDistance >= PULL_THRESHOLD && !isRefreshing) {
      setIsRefreshing(true);
      setPullDistance(PULL_THRESHOLD * 0.6);
      if (navigator.vibrate) navigator.vibrate(15);

      try {
        await onRefresh();
      } catch { /* ignore */ }

      setIsRefreshing(false);
    }
    setPullDistance(0);
  }, [enabled, pullDistance, isRefreshing, onRefresh]);

  const handlers = {
    onTouchStart,
    onTouchMove,
    onTouchEnd,
  };

  const progress = Math.min(pullDistance / PULL_THRESHOLD, 1);

  return { pullDistance, isRefreshing, progress, handlers };
}

export default usePullToRefresh;
