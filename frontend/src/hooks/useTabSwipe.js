import { useRef, useCallback } from 'react';

const SWIPE_THRESHOLD = 80;
const EDGE_ZONE = 20;

const SWIPEABLE_TABS = ['dashboard', 'notes', 'gallery', 'graph', 'chat'];

// Tabs with internal multi-panel swipe — skip tab navigation on these
const MULTI_PANEL_TABS = new Set(['notes', 'gallery', 'chat', 'documents', 'upload', 'journal']);

/**
 * useTabSwipe - Horizontal swipe to navigate between bottom nav tabs.
 * Also detects left-edge swipe to open the nav drawer.
 *
 * Returns touch handlers, navDirection ref, and directionTabChange
 * (a wrapped onTabChange that also sets animation direction).
 */
export function useTabSwipe({ activeTab, onTabChange, onOpenDrawer, enabled }) {
  const touchRef = useRef({ startX: 0, startY: 0, edgeSwipe: false });
  const navDirection = useRef(1);

  // Wrapped tab change that sets animation direction for non-swipe navigations (taps)
  const directionTabChange = useCallback((tabId) => {
    const oldIdx = SWIPEABLE_TABS.indexOf(activeTab);
    const newIdx = SWIPEABLE_TABS.indexOf(tabId);
    if (oldIdx !== -1 && newIdx !== -1) navDirection.current = newIdx > oldIdx ? 1 : -1;
    onTabChange(tabId);
  }, [activeTab, onTabChange]);

  const onTouchStart = useCallback((e) => {
    if (!enabled) return;
    const t = e.touches[0];
    touchRef.current = {
      startX: t.clientX,
      startY: t.clientY,
      edgeSwipe: t.clientX < EDGE_ZONE,
    };
  }, [enabled]);

  const onTouchEnd = useCallback((e) => {
    if (!enabled) return;
    const dx = e.changedTouches[0].clientX - touchRef.current.startX;
    const dy = e.changedTouches[0].clientY - touchRef.current.startY;

    // Only horizontal gestures
    if (Math.abs(dy) > Math.abs(dx) || Math.abs(dx) < SWIPE_THRESHOLD) return;

    // Edge swipe to open drawer
    if (touchRef.current.edgeSwipe && dx > SWIPE_THRESHOLD) {
      onOpenDrawer?.();
      return;
    }

    // Skip tab navigation on multi-panel tabs (they have internal swipe)
    if (MULTI_PANEL_TABS.has(activeTab)) return;

    // Tab navigation
    const idx = SWIPEABLE_TABS.indexOf(activeTab);
    if (idx === -1) return;

    if (dx < -SWIPE_THRESHOLD && idx < SWIPEABLE_TABS.length - 1) {
      navDirection.current = 1; // forward
      onTabChange(SWIPEABLE_TABS[idx + 1]);
    } else if (dx > SWIPE_THRESHOLD && idx > 0) {
      navDirection.current = -1; // backward
      onTabChange(SWIPEABLE_TABS[idx - 1]);
    }
  }, [enabled, activeTab, onTabChange, onOpenDrawer]);

  return {
    touchHandlers: enabled ? { onTouchStart, onTouchEnd } : {},
    navDirection,
    directionTabChange,
    SWIPEABLE_TABS,
  };
}

export default useTabSwipe;
