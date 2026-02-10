import React, { useEffect, useRef } from 'react';
import { CheckSquare, Link2, Hash, Smile } from 'lucide-react';
import './CommandMenu.css';

const COMMANDS = [
  { name: '/todo', icon: CheckSquare, description: 'Create a task', prefix: '/todo ' },
  { name: '/link', icon: Link2, description: 'Link a note', prefix: '/link ' },
  { name: '/tag', icon: Hash, description: 'Add a tag', prefix: '/tag ' },
  { name: '/mood', icon: Smile, description: 'Set mood', prefix: '/mood ' },
];

/**
 * CommandMenu - Dropdown overlay showing available slash commands.
 *
 * Props:
 * - filter: current typed text after "/" (e.g. "to" when user typed "/to")
 * - selectedIndex: currently highlighted item
 * - onSelect: (prefix) => void
 * - onClose: () => void
 */
function CommandMenu({ filter, selectedIndex, onSelect, onClose }) {
  const menuRef = useRef(null);

  const filtered = COMMANDS.filter(cmd =>
    cmd.name.slice(1).startsWith(filter.toLowerCase())
  );

  // Scroll selected item into view
  useEffect(() => {
    if (!menuRef.current) return;
    const selected = menuRef.current.querySelector('.command-menu-item--selected');
    if (selected) {
      selected.scrollIntoView({ block: 'nearest' });
    }
  }, [selectedIndex]);

  if (filtered.length === 0) return null;

  return (
    <div className="command-menu" ref={menuRef}>
      <div className="command-menu-header">Commands</div>
      {filtered.map((cmd, index) => {
        const Icon = cmd.icon;
        return (
          <button
            key={cmd.name}
            className={`command-menu-item ${index === selectedIndex ? 'command-menu-item--selected' : ''}`}
            onClick={() => onSelect(cmd.prefix)}
            onMouseEnter={() => {/* parent manages index */}}
          >
            <Icon size={14} className="command-menu-icon" />
            <span className="command-menu-name">{cmd.name}</span>
            <span className="command-menu-desc">{cmd.description}</span>
          </button>
        );
      })}
      <div className="command-menu-hint">
        <kbd>↑↓</kbd> navigate
        <kbd>Enter</kbd> select
        <kbd>Esc</kbd> close
      </div>
    </div>
  );
}

// Export the command list for parent filtering
export { COMMANDS };
export default CommandMenu;
