/**
 * Toast - Individual toast notification component.
 *
 * Features:
 * - Neural Glass styling with backdrop-blur
 * - Color-coded by type (success, error, warning, info)
 * - lucide-react icons per type
 * - Close button for manual dismiss
 * - Animated progress bar showing auto-dismiss countdown
 * - Framer Motion entrance/exit animations
 */

import React, { useEffect, useRef, useCallback } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react';

const ICON_MAP = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
};

const slideVariants = {
  initial: { x: 120, opacity: 0, scale: 0.95 },
  animate: { x: 0, opacity: 1, scale: 1, transition: { duration: 0.3, ease: [0, 0, 0.2, 1] } },
  exit: { x: 80, opacity: 0, scale: 0.95, transition: { duration: 0.2, ease: [0.4, 0, 1, 1] } },
};

function Toast({ toast, onRemove }) {
  const { id, type, message, description, duration } = toast;
  const timerRef = useRef(null);
  const progressRef = useRef(null);

  const IconComponent = ICON_MAP[type] || Info;

  const dismiss = useCallback(() => {
    onRemove(id);
  }, [id, onRemove]);

  // Auto-dismiss timer with progress bar
  useEffect(() => {
    if (duration <= 0) return;

    // Start CSS animation for progress bar
    if (progressRef.current) {
      progressRef.current.style.animationDuration = `${duration}ms`;
    }

    timerRef.current = setTimeout(dismiss, duration);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [duration, dismiss]);

  return (
    <motion.div
      layout
      variants={slideVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className={`toast-item toast-${type}`}
      role="alert"
      aria-live={type === 'error' ? 'assertive' : 'polite'}
    >
      <div className="toast-icon">
        <IconComponent size={18} />
      </div>

      <div className="toast-body">
        <p className="toast-message">{message}</p>
        {description && <p className="toast-description">{description}</p>}
        {toast.action && (
          <button
            className="toast-action"
            onClick={(e) => {
              e.stopPropagation();
              toast.action.onClick();
              dismiss();
            }}
          >
            {toast.action.label}
          </button>
        )}
      </div>

      <button
        className="toast-close"
        onClick={dismiss}
        aria-label="Dismiss notification"
      >
        <X size={14} />
      </button>

      {duration > 0 && (
        <div className="toast-progress-track">
          <div
            ref={progressRef}
            className={`toast-progress-bar toast-progress-${type}`}
          />
        </div>
      )}
    </motion.div>
  );
}

export default React.memo(Toast);
