import { useEffect, useState, useCallback } from 'react';

const KEYBOARD_THRESHOLD = 150;

/**
 * useViewportHeight - Dynamically sets --ng-viewport-height CSS variable
 * using the Visual Viewport API for accurate mobile height.
 *
 * Also detects on-screen keyboard state by comparing visualViewport.height
 * against window.innerHeight. Returns { isKeyboardOpen, keyboardHeight }.
 */
export function useViewportHeight() {
  const [isKeyboardOpen, setIsKeyboardOpen] = useState(false);
  const [keyboardHeight, setKeyboardHeight] = useState(0);

  const update = useCallback(() => {
    const vv = window.visualViewport;
    if (!vv) return;

    const vvHeight = vv.height;
    const winHeight = window.innerHeight;
    const diff = winHeight - vvHeight;
    const kbOpen = diff > KEYBOARD_THRESHOLD;

    document.documentElement.style.setProperty(
      '--ng-viewport-height',
      `${vvHeight}px`
    );

    setIsKeyboardOpen(kbOpen);
    setKeyboardHeight(kbOpen ? diff : 0);
  }, []);

  useEffect(() => {
    const vv = window.visualViewport;
    if (!vv) return;

    update();
    vv.addEventListener('resize', update);
    vv.addEventListener('scroll', update);

    return () => {
      vv.removeEventListener('resize', update);
      vv.removeEventListener('scroll', update);
    };
  }, [update]);

  return { isKeyboardOpen, keyboardHeight };
}

export default useViewportHeight;
