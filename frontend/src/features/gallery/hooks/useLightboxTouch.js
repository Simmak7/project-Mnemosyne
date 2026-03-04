import { useState, useCallback, useRef } from 'react';

const SWIPE_THRESHOLD = 60;
const DISMISS_THRESHOLD = 120;
const DOUBLE_TAP_MS = 300;

/**
 * useLightboxTouch - Swipe navigation, drag-dismiss, and double-tap for lightbox.
 */
export function useLightboxTouch({ onNavigate, onClose, onDoubleTap, isZoomed }) {
  const [dismissProgress, setDismissProgress] = useState(0);
  const touchRef = useRef({
    startX: 0, startY: 0,
    lastTap: 0,
    axis: null, // 'x' | 'y' | null
  });

  const onTouchStart = useCallback((e) => {
    if (e.touches.length !== 1) return;
    e.stopPropagation();
    const t = e.touches[0];
    touchRef.current.startX = t.clientX;
    touchRef.current.startY = t.clientY;
    touchRef.current.axis = null;

    // Double tap detection
    const now = Date.now();
    if (now - touchRef.current.lastTap < DOUBLE_TAP_MS) {
      touchRef.current.lastTap = 0;
      onDoubleTap?.();
      return;
    }
    touchRef.current.lastTap = now;
  }, [onDoubleTap]);

  const onTouchMove = useCallback((e) => {
    if (e.touches.length !== 1 || isZoomed) return;
    const dx = e.touches[0].clientX - touchRef.current.startX;
    const dy = e.touches[0].clientY - touchRef.current.startY;

    // Lock axis on first significant movement
    if (!touchRef.current.axis && (Math.abs(dx) > 10 || Math.abs(dy) > 10)) {
      touchRef.current.axis = Math.abs(dy) > Math.abs(dx) ? 'y' : 'x';
    }

    // Vertical drag-to-dismiss (only downward)
    if (touchRef.current.axis === 'y' && dy > 0) {
      e.preventDefault();
      setDismissProgress(Math.min(dy / DISMISS_THRESHOLD, 1));
    }
  }, [isZoomed]);

  const onTouchEnd = useCallback((e) => {
    e.stopPropagation();
    if (isZoomed) return;
    const dx = e.changedTouches[0].clientX - touchRef.current.startX;
    const dy = e.changedTouches[0].clientY - touchRef.current.startY;

    // Dismiss if dragged far enough
    if (touchRef.current.axis === 'y' && dismissProgress >= 1) {
      onClose();
      setDismissProgress(0);
      return;
    }

    // Horizontal swipe navigation
    if (touchRef.current.axis === 'x' && Math.abs(dx) > SWIPE_THRESHOLD) {
      onNavigate(dx < 0 ? 'next' : 'prev');
    }

    setDismissProgress(0);
    touchRef.current.axis = null;
  }, [dismissProgress, isZoomed, onClose, onNavigate]);

  return { onTouchStart, onTouchMove, onTouchEnd, dismissProgress };
}

export default useLightboxTouch;
