/**
 * ConfirmDialog - Glass-styled replacement for window.confirm.
 *
 * Portal-based modal with backdrop blur, title, message, and
 * confirm/cancel buttons. Used via useConfirm() hook which
 * returns a promise that resolves to true/false.
 *
 * Usage:
 *   const confirm = useConfirm();
 *   const yes = await confirm('Delete image?', 'This cannot be undone.');
 */

import React, { useEffect, useRef, useCallback } from 'react';
import ReactDOM from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle } from 'lucide-react';

const backdropVariants = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: 0.2 } },
  exit: { opacity: 0, transition: { duration: 0.15 } },
};

const dialogVariants = {
  initial: { opacity: 0, scale: 0.95, y: 8 },
  animate: { opacity: 1, scale: 1, y: 0, transition: { duration: 0.25, ease: [0, 0, 0.2, 1] } },
  exit: { opacity: 0, scale: 0.95, y: 8, transition: { duration: 0.15 } },
};

function ConfirmDialog({ title, message, onConfirm, onCancel }) {
  const confirmBtnRef = useRef(null);
  const dialogRef = useRef(null);

  // Focus the cancel button on mount, trap focus inside dialog
  useEffect(() => {
    if (confirmBtnRef.current) {
      confirmBtnRef.current.focus();
    }
  }, []);

  // Handle Escape key
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      onCancel();
    }
  }, [onCancel]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // Prevent body scroll when dialog is open
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);

  const content = (
    <AnimatePresence>
      <motion.div
        className="confirm-backdrop"
        variants={backdropVariants}
        initial="initial"
        animate="animate"
        exit="exit"
        onClick={onCancel}
      >
        <motion.div
          ref={dialogRef}
          className="confirm-dialog"
          variants={dialogVariants}
          initial="initial"
          animate="animate"
          exit="exit"
          onClick={(e) => e.stopPropagation()}
          role="alertdialog"
          aria-modal="true"
          aria-labelledby="confirm-title"
          aria-describedby="confirm-message"
        >
          <div className="confirm-icon">
            <AlertTriangle size={24} />
          </div>

          <h3 id="confirm-title" className="confirm-title">{title}</h3>
          {message && (
            <p id="confirm-message" className="confirm-message">{message}</p>
          )}

          <div className="confirm-actions">
            <button
              className="confirm-btn confirm-btn-cancel"
              onClick={onCancel}
            >
              Cancel
            </button>
            <button
              ref={confirmBtnRef}
              className="confirm-btn confirm-btn-confirm"
              onClick={onConfirm}
            >
              Confirm
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );

  return ReactDOM.createPortal(content, document.body);
}

export default React.memo(ConfirmDialog);
