/**
 * SidebarCustomizer - Popover to toggle sidebar sections visibility.
 * Opens from the gear icon in the sidebar footer.
 */

import React, { useRef, useEffect } from 'react';
import { X, RotateCcw } from 'lucide-react';
import './SidebarCustomizer.css';

function SidebarCustomizer({ allItems, isTabVisible, onToggle, onReset, onClose }) {
  const ref = useRef(null);

  // Close on outside click
  useEffect(() => {
    const handleClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) onClose();
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [onClose]);

  // Close on Escape
  useEffect(() => {
    const handleKey = (e) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [onClose]);

  const allTabIds = allItems.map(i => i.id);

  return (
    <div ref={ref} className="sidebar-customizer">
      <div className="customizer-header">
        <span className="customizer-title">Customize Sidebar</span>
        <button className="customizer-close" onClick={onClose} aria-label="Close">
          <X size={16} />
        </button>
      </div>

      <div className="customizer-list">
        {allItems.map(item => {
          const visible = isTabVisible(item.id);
          const isHome = item.id === 'dashboard';
          const Icon = item.iconComponent;
          return (
            <label
              key={item.id}
              className={`customizer-item ${isHome ? 'locked' : ''}`}
            >
              <Icon size={16} className="customizer-item-icon" />
              <span className="customizer-item-label">{item.label}</span>
              <input
                type="checkbox"
                checked={visible}
                disabled={isHome}
                onChange={() => onToggle(item.id, allTabIds)}
                className="customizer-toggle"
              />
            </label>
          );
        })}
      </div>

      <button className="customizer-reset" onClick={onReset}>
        <RotateCcw size={14} />
        <span>Reset to defaults</span>
      </button>
    </div>
  );
}

export default SidebarCustomizer;
