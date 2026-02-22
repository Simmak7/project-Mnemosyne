/**
 * ToastProvider - Global toast notification context provider
 *
 * Provides useToast() hook for showing notifications anywhere in the app.
 * Manages toast stack, auto-dismiss timers, and confirm dialogs.
 *
 * Usage:
 *   const { showSuccess, showError, showWarning, showInfo } = useToast();
 *   showSuccess('Image uploaded successfully');
 *   showError('Failed to connect', { description: 'Check network' });
 */

import React, { createContext, useContext, useCallback, useReducer } from 'react';
import ToastContainer from './ToastContainer';
import ConfirmDialog from './ConfirmDialog';

const ToastContext = createContext(null);

const MAX_VISIBLE = 3;
const DEFAULT_DURATION = 5000;

let toastIdCounter = 0;
function generateId() {
  return `toast-${++toastIdCounter}-${Date.now()}`;
}

// Reducer for toast state
function toastReducer(state, action) {
  switch (action.type) {
    case 'ADD_TOAST': {
      const toasts = [action.payload, ...state.toasts].slice(0, MAX_VISIBLE);
      return { ...state, toasts };
    }
    case 'REMOVE_TOAST':
      return {
        ...state,
        toasts: state.toasts.filter(t => t.id !== action.payload),
      };
    case 'SET_CONFIRM':
      return { ...state, confirm: action.payload };
    case 'CLEAR_CONFIRM':
      return { ...state, confirm: null };
    default:
      return state;
  }
}

const initialState = { toasts: [], confirm: null };

export function ToastProvider({ children }) {
  const [state, dispatch] = useReducer(toastReducer, initialState);

  const removeToast = useCallback((id) => {
    dispatch({ type: 'REMOVE_TOAST', payload: id });
  }, []);

  const showToast = useCallback(({ type = 'info', message, description, duration = DEFAULT_DURATION }) => {
    const id = generateId();
    dispatch({
      type: 'ADD_TOAST',
      payload: { id, type, message, description, duration, createdAt: Date.now() },
    });
    return id;
  }, []);

  const showSuccess = useCallback((message, opts = {}) => {
    return showToast({ type: 'success', message, ...opts });
  }, [showToast]);

  const showError = useCallback((message, opts = {}) => {
    return showToast({ type: 'error', message, duration: 8000, ...opts });
  }, [showToast]);

  const showWarning = useCallback((message, opts = {}) => {
    return showToast({ type: 'warning', message, duration: 6000, ...opts });
  }, [showToast]);

  const showInfo = useCallback((message, opts = {}) => {
    return showToast({ type: 'info', message, ...opts });
  }, [showToast]);

  // Promise-based confirm dialog
  const confirm = useCallback((title, message) => {
    return new Promise((resolve) => {
      dispatch({
        type: 'SET_CONFIRM',
        payload: { title, message, resolve },
      });
    });
  }, []);

  const handleConfirmResolve = useCallback((result) => {
    if (state.confirm?.resolve) {
      state.confirm.resolve(result);
    }
    dispatch({ type: 'CLEAR_CONFIRM' });
  }, [state.confirm]);

  const value = React.useMemo(() => ({
    showToast, showSuccess, showError, showWarning, showInfo, confirm,
  }), [showToast, showSuccess, showError, showWarning, showInfo, confirm]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastContainer toasts={state.toasts} onRemove={removeToast} />
      {state.confirm && (
        <ConfirmDialog
          title={state.confirm.title}
          message={state.confirm.message}
          onConfirm={() => handleConfirmResolve(true)}
          onCancel={() => handleConfirmResolve(false)}
        />
      )}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}

export function useConfirm() {
  const { confirm } = useToast();
  return confirm;
}

export default ToastProvider;
