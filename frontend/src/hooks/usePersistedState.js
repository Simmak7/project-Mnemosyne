import { useState, useEffect } from 'react';

/**
 * usePersistedState - localStorage-backed useState
 * Reads initial value from localStorage, writes on every update.
 * Falls back to defaultValue when no stored value exists.
 *
 * @param {string} key - localStorage key (prefixed with 'mnemosyne:')
 * @param {*} defaultValue - fallback when nothing stored
 * @returns {[*, Function]} same API as useState
 */
export function usePersistedState(key, defaultValue) {
  const storageKey = `mnemosyne:${key}`;

  const [value, setValue] = useState(() => {
    try {
      const stored = localStorage.getItem(storageKey);
      if (stored === null) return defaultValue;
      return JSON.parse(stored);
    } catch {
      return defaultValue;
    }
  });

  // Sync to localStorage on change
  useEffect(() => {
    try {
      if (value === null || value === undefined) {
        localStorage.removeItem(storageKey);
      } else {
        localStorage.setItem(storageKey, JSON.stringify(value));
      }
    } catch {
      // localStorage full or unavailable - ignore
    }
  }, [storageKey, value]);

  return [value, setValue];
}

export default usePersistedState;
