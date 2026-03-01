import { useState, useEffect } from 'react';

const MOBILE_BREAKPOINT = 767;
const mediaQuery = `(max-width: ${MOBILE_BREAKPOINT}px)`;

/**
 * useIsMobile - Reactive mobile detection hook.
 * Uses matchMedia for efficient boundary-crossing detection.
 * Returns true when viewport <= 767px.
 */
export function useIsMobile() {
  const [isMobile, setIsMobile] = useState(() => {
    if (typeof window === 'undefined') return false;
    return window.matchMedia(mediaQuery).matches;
  });

  useEffect(() => {
    const mql = window.matchMedia(mediaQuery);
    const handler = (e) => setIsMobile(e.matches);

    mql.addEventListener('change', handler);
    return () => mql.removeEventListener('change', handler);
  }, []);

  return isMobile;
}

export default useIsMobile;
