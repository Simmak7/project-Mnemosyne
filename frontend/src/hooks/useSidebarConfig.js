/**
 * useSidebarConfig - Manages which sidebar tabs are visible
 * Persists to localStorage so preferences survive page refresh.
 * 'dashboard' is always visible (cannot be hidden).
 */

import { useState, useCallback } from 'react';

const STORAGE_KEY = 'sidebar:hidden-tabs';
const ALWAYS_VISIBLE = ['dashboard'];

function loadHiddenTabs() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

function saveHiddenTabs(tabs) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(tabs));
  } catch { /* ignore */ }
}

export function useSidebarConfig() {
  const [hiddenTabs, setHiddenTabs] = useState(loadHiddenTabs);

  const isTabVisible = useCallback((tabId) => {
    if (ALWAYS_VISIBLE.includes(tabId)) return true;
    return !hiddenTabs.includes(tabId);
  }, [hiddenTabs]);

  const toggleTab = useCallback((tabId, allTabIds) => {
    if (ALWAYS_VISIBLE.includes(tabId)) return;

    setHiddenTabs(prev => {
      let next;
      if (prev.includes(tabId)) {
        // Unhide
        next = prev.filter(id => id !== tabId);
      } else {
        // Hide — but ensure at least 1 non-dashboard tab remains visible
        const visibleNonHome = allTabIds.filter(
          id => !ALWAYS_VISIBLE.includes(id) && !prev.includes(id) && id !== tabId
        );
        if (visibleNonHome.length === 0) return prev; // Can't hide last one
        next = [...prev, tabId];
      }
      saveHiddenTabs(next);
      return next;
    });
  }, []);

  const resetDefaults = useCallback(() => {
    setHiddenTabs([]);
    saveHiddenTabs([]);
  }, []);

  return { hiddenTabs, isTabVisible, toggleTab, resetDefaults };
}

export default useSidebarConfig;
