import React, { useRef, useState, useCallback } from 'react';
import { useIsMobile } from '../hooks/useIsMobile';
import './SwipeableCard.css';

const SWIPE_THRESHOLD = 60;
const ACTION_WIDTH = 72;

/**
 * SwipeableCard - Wraps a card with swipe-to-reveal actions on mobile.
 * Swipe left reveals right actions, swipe right reveals left actions.
 */
function SwipeableCard({ children, leftAction, rightAction }) {
  const isMobile = useIsMobile();
  const [translateX, setTranslateX] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);
  const touchRef = useRef({ startX: 0, startY: 0, tracking: false });

  const handleTouchStart = useCallback((e) => {
    if (isAnimating) return;
    const touch = e.touches[0];
    touchRef.current = { startX: touch.clientX, startY: touch.clientY, tracking: true };
  }, [isAnimating]);

  const handleTouchMove = useCallback((e) => {
    const ref = touchRef.current;
    if (!ref.tracking) return;

    const dx = e.touches[0].clientX - ref.startX;
    const dy = e.touches[0].clientY - ref.startY;

    // If vertical scroll dominates, stop tracking
    if (Math.abs(dy) > Math.abs(dx) && Math.abs(dx) < 10) {
      ref.tracking = false;
      setTranslateX(0);
      return;
    }

    // Clamp swipe range
    const maxLeft = rightAction ? -ACTION_WIDTH : 0;
    const maxRight = leftAction ? ACTION_WIDTH : 0;
    const clamped = Math.max(maxLeft, Math.min(maxRight, dx * 0.6));
    setTranslateX(clamped);
  }, [leftAction, rightAction]);

  const handleTouchEnd = useCallback((e) => {
    const wasTracking = touchRef.current.tracking;
    touchRef.current.tracking = false;

    if (Math.abs(translateX) >= SWIPE_THRESHOLD) {
      // Snap open — stop propagation to prevent tab/panel swipe
      if (wasTracking) e.stopPropagation();
      const target = translateX > 0 ? ACTION_WIDTH : -ACTION_WIDTH;
      setIsAnimating(true);
      setTranslateX(target);
      setTimeout(() => setIsAnimating(false), 250);
    } else if (translateX !== 0) {
      // Snap closed — still consumed the gesture
      if (wasTracking) e.stopPropagation();
      setIsAnimating(true);
      setTranslateX(0);
      setTimeout(() => setIsAnimating(false), 250);
    }
  }, [translateX]);

  const handleActionClick = useCallback((action) => {
    if (navigator.vibrate) navigator.vibrate(10);
    setIsAnimating(true);
    setTranslateX(0);
    setTimeout(() => {
      setIsAnimating(false);
      action?.onAction();
    }, 200);
  }, []);

  // Reset on outside tap
  const handleCardClick = useCallback((e) => {
    if (translateX !== 0) {
      e.stopPropagation();
      e.preventDefault();
      setIsAnimating(true);
      setTranslateX(0);
      setTimeout(() => setIsAnimating(false), 250);
    }
  }, [translateX]);

  // Desktop: no wrapping needed
  if (!isMobile) return children;

  return (
    <div className={`swipeable-card-container${translateX !== 0 ? ' swiping' : ''}`}>
      {/* Left action (revealed on swipe right) */}
      {leftAction && (
        <button
          className={`swipe-action swipe-action-left ${leftAction.className || ''}`}
          style={{ background: leftAction.color }}
          onClick={() => handleActionClick(leftAction)}
        >
          {leftAction.icon}
          <span className="swipe-action-label">{leftAction.label}</span>
        </button>
      )}

      {/* Right action (revealed on swipe left) */}
      {rightAction && (
        <button
          className={`swipe-action swipe-action-right ${rightAction.className || ''}`}
          style={{ background: rightAction.color }}
          onClick={() => handleActionClick(rightAction)}
        >
          {rightAction.icon}
          <span className="swipe-action-label">{rightAction.label}</span>
        </button>
      )}

      {/* Card content */}
      <div
        className={`swipeable-card-content ${isAnimating ? 'animating' : ''}`}
        style={{ transform: `translateX(${translateX}px)` }}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        onClickCapture={handleCardClick}
      >
        {children}
      </div>
    </div>
  );
}

export default SwipeableCard;
