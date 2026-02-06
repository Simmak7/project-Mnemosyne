/**
 * useTheme - Theme/dark mode state and handlers
 */
import { useState, useLayoutEffect, useCallback } from 'react';

const ACCENT_COLORS = {
  blue: { primary: '#3B82F6', hover: '#2563EB', light: '#DBEAFE' },
  purple: { primary: '#8B5CF6', hover: '#7C3AED', light: '#EDE9FE' },
  green: { primary: '#10B981', hover: '#059669', light: '#D1FAE5' },
  orange: { primary: '#F59E0B', hover: '#D97706', light: '#FEF3C7' },
  pink: { primary: '#EC4899', hover: '#DB2777', light: '#FCE7F3' },
};

const DENSITY_VALUES = {
  compact: { spacing: '8px', padding: '12px', fontSize: '13px' },
  comfortable: { spacing: '16px', padding: '16px', fontSize: '14px' },
  spacious: { spacing: '24px', padding: '20px', fontSize: '15px' },
};

export function useTheme() {
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved ? JSON.parse(saved) : false;
  });

  // Apply dark mode to document
  useLayoutEffect(() => {
    document.documentElement.setAttribute('data-theme', isDarkMode ? 'dark' : 'light');
    localStorage.setItem('darkMode', JSON.stringify(isDarkMode));
  }, [isDarkMode]);

  // Apply saved accent color and UI density on load
  useLayoutEffect(() => {
    const root = document.documentElement;

    // Apply accent color
    const savedAccentColor = localStorage.getItem('accentColor');
    if (savedAccentColor) {
      const colors = ACCENT_COLORS[savedAccentColor] || ACCENT_COLORS.blue;
      root.style.setProperty('--accent-color', colors.primary);
      root.style.setProperty('--accent-hover', colors.hover);
      root.style.setProperty('--accent-light', colors.light);
    }

    // Apply UI density
    const savedDensity = localStorage.getItem('uiDensity');
    if (savedDensity) {
      const density = DENSITY_VALUES[savedDensity] || DENSITY_VALUES.comfortable;
      root.style.setProperty('--density-spacing', density.spacing);
      root.style.setProperty('--density-padding', density.padding);
      root.style.setProperty('--density-font-size', density.fontSize);
      root.setAttribute('data-density', savedDensity);
    }
  }, []);

  const toggleDarkMode = useCallback(() => {
    setIsDarkMode(prev => !prev);
  }, []);

  return {
    isDarkMode,
    toggleDarkMode,
  };
}

export default useTheme;
