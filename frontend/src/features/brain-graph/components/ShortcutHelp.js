/**
 * ShortcutHelp - Keyboard shortcut overlay for Brain Graph
 *
 * Shows all available shortcuts when user presses "?".
 * Organized by category: navigation, views, actions, canvas.
 */

import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import './ShortcutHelp.css';

const SHORTCUT_GROUPS = [
  {
    title: 'Views',
    shortcuts: [
      { keys: ['1'], action: 'Map view' },
      { keys: ['2'], action: 'Explore view' },
      { keys: ['3'], action: 'Media view' },
      { keys: ['4'], action: 'PathFinder view' },
    ],
  },
  {
    title: 'Selection',
    shortcuts: [
      { keys: ['Click'], action: 'Select node' },
      { keys: ['Right-click'], action: 'Open in editor' },
      { keys: ['Esc'], action: 'Clear selection' },
      { keys: ['P'], action: 'Pin / unpin node' },
      { keys: ['F'], action: 'Expand neighbors' },
    ],
  },
  {
    title: 'Navigation',
    shortcuts: [
      { keys: ['Alt', '\u2190'], action: 'Go back' },
      { keys: ['Alt', '\u2192'], action: 'Go forward' },
      { keys: ['C'], action: 'Center on focus' },
    ],
  },
  {
    title: 'Canvas',
    shortcuts: [
      { keys: ['+'], action: 'Zoom in' },
      { keys: ['-'], action: 'Zoom out' },
      { keys: ['0'], action: 'Reset zoom' },
      { keys: ['\u2190\u2191\u2193\u2192'], action: 'Pan canvas' },
      { keys: ['Space'], action: 'Pause simulation' },
      { keys: ['?'], action: 'Toggle this help' },
    ],
  },
];

export function ShortcutHelp({ isOpen, onClose }) {
  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (e) => {
      if (e.key === 'Escape' || e.key === '?') onClose();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="shortcut-help__backdrop" onClick={onClose}>
      <div className="shortcut-help" onClick={(e) => e.stopPropagation()}>
        <div className="shortcut-help__header">
          <h3>Keyboard Shortcuts</h3>
          <button className="shortcut-help__close" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <div className="shortcut-help__grid">
          {SHORTCUT_GROUPS.map((group) => (
            <div key={group.title} className="shortcut-help__group">
              <h4 className="shortcut-help__group-title">{group.title}</h4>
              {group.shortcuts.map((item, i) => (
                <div key={i} className="shortcut-help__row">
                  <div className="shortcut-help__keys">
                    {item.keys.map((key, j) => (
                      <React.Fragment key={j}>
                        {j > 0 && <span className="shortcut-help__plus">+</span>}
                        <kbd className="shortcut-help__kbd">{key}</kbd>
                      </React.Fragment>
                    ))}
                  </div>
                  <span className="shortcut-help__action">{item.action}</span>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default ShortcutHelp;
