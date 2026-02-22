/**
 * ToastContainer - Fixed-position container rendering the toast stack.
 *
 * Positioned top-right, uses Framer Motion for slide-in/fade-out animations.
 * Uses Neural Glass z-index layer (--ng-z-toast: 1700).
 */

import React from 'react';
import { AnimatePresence } from 'framer-motion';
import Toast from './Toast';
import './Toast.css';

function ToastContainer({ toasts, onRemove }) {
  return (
    <div
      className="toast-container"
      role="region"
      aria-label="Notifications"
      aria-live="polite"
    >
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <Toast key={toast.id} toast={toast} onRemove={onRemove} />
        ))}
      </AnimatePresence>
    </div>
  );
}

export default React.memo(ToastContainer);
