import { useState, useCallback, useRef } from 'react';

/**
 * usePinchZoom - Two-finger pinch-to-zoom for images.
 * Returns scale, transform origin, touch handlers, and reset.
 */
export function usePinchZoom({ minScale = 1, maxScale = 4 } = {}) {
  const [scale, setScale] = useState(1);
  const [translate, setTranslate] = useState({ x: 0, y: 0 });
  const pinchRef = useRef({ initialDist: 0, initialScale: 1, active: false });
  const panRef = useRef({ lastX: 0, lastY: 0 });

  const getDistance = (t1, t2) =>
    Math.hypot(t2.clientX - t1.clientX, t2.clientY - t1.clientY);

  const onTouchStart = useCallback((e) => {
    if (e.touches.length === 2) {
      pinchRef.current = {
        initialDist: getDistance(e.touches[0], e.touches[1]),
        initialScale: scale,
        active: true,
      };
    } else if (e.touches.length === 1 && scale > 1.05) {
      // Pan when zoomed
      panRef.current = { lastX: e.touches[0].clientX, lastY: e.touches[0].clientY };
    }
  }, [scale]);

  const onTouchMove = useCallback((e) => {
    if (pinchRef.current.active && e.touches.length === 2) {
      e.preventDefault();
      const dist = getDistance(e.touches[0], e.touches[1]);
      const ratio = dist / pinchRef.current.initialDist;
      const newScale = Math.max(minScale, Math.min(maxScale,
        pinchRef.current.initialScale * ratio
      ));
      setScale(newScale);
    } else if (e.touches.length === 1 && scale > 1.05) {
      // Pan while zoomed
      e.preventDefault();
      const dx = e.touches[0].clientX - panRef.current.lastX;
      const dy = e.touches[0].clientY - panRef.current.lastY;
      panRef.current = { lastX: e.touches[0].clientX, lastY: e.touches[0].clientY };
      setTranslate(prev => ({ x: prev.x + dx, y: prev.y + dy }));
    }
  }, [minScale, maxScale, scale]);

  const onTouchEnd = useCallback((e) => {
    if (e.touches.length < 2) {
      pinchRef.current.active = false;
      // Snap back to 1x if below threshold
      if (scale < 1.1) {
        setScale(1);
        setTranslate({ x: 0, y: 0 });
      }
    }
  }, [scale]);

  const reset = useCallback(() => {
    setScale(1);
    setTranslate({ x: 0, y: 0 });
  }, []);

  const toggleZoom = useCallback(() => {
    if (scale > 1.05) {
      setScale(1);
      setTranslate({ x: 0, y: 0 });
    } else {
      setScale(2);
    }
  }, [scale]);

  return {
    scale,
    translate,
    isZoomed: scale > 1.05,
    handlers: { onTouchStart, onTouchMove, onTouchEnd },
    reset,
    toggleZoom,
  };
}

export default usePinchZoom;
