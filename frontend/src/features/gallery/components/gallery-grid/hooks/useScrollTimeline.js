import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Hook for scroll-based timeline tracking and navigation
 */
export function useScrollTimeline(containerRef, layoutRows, virtualizer) {
  const [activeTimelineMarker, setActiveTimelineMarker] = useState(null);
  const rafRef = useRef(null);

  // Track scroll position for timeline (throttled to rAF)
  const handleScroll = useCallback(() => {
    if (rafRef.current) return;
    rafRef.current = requestAnimationFrame(() => {
      rafRef.current = null;
      if (!containerRef.current) return;

      const items = virtualizer.getVirtualItems();

      for (const item of items) {
        const row = layoutRows[item.index];
        if (row?.type === 'image-row' && row.date) {
          const date = new Date(row.date);
          const markerKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
          setActiveTimelineMarker(markerKey);
          break;
        }
      }
    });
  }, [layoutRows, virtualizer, containerRef]);

  // Cleanup rAF on unmount
  useEffect(() => {
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  // Set initial active marker when images load
  useEffect(() => {
    if (layoutRows.length > 0 && !activeTimelineMarker) {
      for (const row of layoutRows) {
        if (row?.type === 'image-row' && row.date) {
          const date = new Date(row.date);
          const markerKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
          setActiveTimelineMarker(markerKey);
          break;
        }
      }
    }
  }, [layoutRows, activeTimelineMarker]);

  // Handle timeline marker click
  const handleTimelineClick = useCallback((marker) => {
    const rowIndex = layoutRows.findIndex(row => {
      if (row.date) {
        const date = new Date(row.date);
        const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        return key === marker.key;
      }
      return false;
    });

    if (rowIndex >= 0) {
      virtualizer.scrollToIndex(rowIndex, { align: 'start' });
    }
  }, [layoutRows, virtualizer]);

  return {
    activeTimelineMarker,
    handleScroll,
    handleTimelineClick,
  };
}
