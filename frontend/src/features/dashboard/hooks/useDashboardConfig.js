/**
 * useDashboardConfig - Persisted react-grid-layout config
 *
 * Stores layouts + hidden widgets in localStorage (v2 key).
 * isCustomizing state is transient (resets on refresh).
 */
import { useState, useCallback, useMemo } from 'react';
import { usePersistedState } from '../../../hooks/usePersistedState';
import { DEFAULT_LAYOUTS } from '../utils/defaultLayouts';
import { getAllWidgetIds } from '../utils/widgetRegistry';

const STORAGE_KEY = 'dashboard:config:v2';

const DEFAULT_CONFIG = {
  layouts: DEFAULT_LAYOUTS,
  hiddenWidgets: [],
};

export function useDashboardConfig() {
  const [config, setConfig] = usePersistedState(STORAGE_KEY, DEFAULT_CONFIG);
  const [isCustomizing, setIsCustomizing] = useState(false);

  const layouts = useMemo(() => {
    const saved = config.layouts || DEFAULT_LAYOUTS;
    const hidden = config.hiddenWidgets || [];
    // Filter out hidden widgets from each breakpoint
    const filtered = {};
    for (const bp of Object.keys(saved)) {
      filtered[bp] = saved[bp].filter(item => !hidden.includes(item.i));
    }
    return filtered;
  }, [config]);

  const visibleWidgets = useMemo(() => {
    const hidden = config.hiddenWidgets || [];
    return getAllWidgetIds().filter(id => !hidden.includes(id));
  }, [config.hiddenWidgets]);

  const isWidgetVisible = useCallback(
    (id) => !(config.hiddenWidgets || []).includes(id),
    [config.hiddenWidgets]
  );

  const toggleWidget = useCallback((id) => {
    setConfig(prev => {
      const hidden = prev.hiddenWidgets || [];
      const isHidden = hidden.includes(id);
      return {
        ...prev,
        hiddenWidgets: isHidden
          ? hidden.filter(h => h !== id)
          : [...hidden, id],
      };
    });
  }, [setConfig]);

  const onLayoutChange = useCallback((_layout, allLayouts) => {
    setConfig(prev => ({ ...prev, layouts: allLayouts }));
  }, [setConfig]);

  const resetToDefaults = useCallback(() => {
    setConfig(DEFAULT_CONFIG);
  }, [setConfig]);

  return {
    layouts,
    visibleWidgets,
    isWidgetVisible,
    toggleWidget,
    onLayoutChange,
    resetToDefaults,
    isCustomizing,
    setIsCustomizing,
  };
}

export default useDashboardConfig;
