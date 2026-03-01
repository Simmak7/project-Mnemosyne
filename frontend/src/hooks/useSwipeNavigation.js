import { useRef, useCallback } from 'react';

const SWIPE_THRESHOLD = 50;

/**
 * useSwipeNavigation - Detects horizontal swipe gestures.
 * Returns a ref to attach to the swipeable container and
 * touch event handlers.
 *
 * @param {Array} panelIds - Ordered array of panel IDs
 * @param {string} activePanel - Current active panel ID
 * @param {function} onPanelChange - Callback with new panel ID
 */
export function useSwipeNavigation(panelIds, activePanel, onPanelChange) {
  const touchStart = useRef({ x: 0, y: 0 });
  const isSwiping = useRef(false);

  const onTouchStart = useCallback((e) => {
    const touch = e.touches[0];
    touchStart.current = { x: touch.clientX, y: touch.clientY };
    isSwiping.current = false;
  }, []);

  const onTouchEnd = useCallback((e) => {
    if (isSwiping.current) return;
    const touch = e.changedTouches[0];
    const dx = touch.clientX - touchStart.current.x;
    const dy = touch.clientY - touchStart.current.y;

    // Only trigger if horizontal movement exceeds threshold
    // and is more horizontal than vertical
    if (Math.abs(dx) < SWIPE_THRESHOLD || Math.abs(dy) > Math.abs(dx)) {
      return;
    }

    const currentIdx = panelIds.indexOf(activePanel);
    if (currentIdx === -1) return;

    if (dx < -SWIPE_THRESHOLD && currentIdx < panelIds.length - 1) {
      // Swipe left -> next panel
      onPanelChange(panelIds[currentIdx + 1]);
    } else if (dx > SWIPE_THRESHOLD && currentIdx > 0) {
      // Swipe right -> previous panel
      onPanelChange(panelIds[currentIdx - 1]);
    }
  }, [panelIds, activePanel, onPanelChange]);

  return { onTouchStart, onTouchEnd };
}

export default useSwipeNavigation;
