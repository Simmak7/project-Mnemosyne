import { useState, useEffect, useRef } from 'react';

/**
 * Hook for measuring container width with resize observer
 * Debounces updates to avoid layout thrashing during panel resize
 */
export function useContainerWidth(containerRef) {
  const [containerWidth, setContainerWidth] = useState(0);
  const timeoutRef = useRef(null);

  useEffect(() => {
    const updateWidthImmediate = () => {
      if (containerRef.current) {
        const width = containerRef.current.offsetWidth - 80;
        setContainerWidth(width);
      }
    };

    const updateWidthDebounced = () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => {
        if (containerRef.current) {
          // Account for timeline scrubber width (60px) and padding
          const width = containerRef.current.offsetWidth - 80;
          setContainerWidth(width);
        }
      }, 150);
    };

    // Initial measurement is immediate
    updateWidthImmediate();
    window.addEventListener('resize', updateWidthDebounced);

    const observer = new ResizeObserver(updateWidthDebounced);
    if (containerRef.current) {
      observer.observe(containerRef.current);
    }

    return () => {
      window.removeEventListener('resize', updateWidthDebounced);
      observer.disconnect();
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [containerRef]);

  return containerWidth;
}
