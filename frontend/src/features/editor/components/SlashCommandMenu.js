import React, { useState, useEffect, useCallback, forwardRef, useImperativeHandle } from 'react';
import {
  Heading1, Heading2, Heading3, List, ListOrdered,
  CheckSquare, Quote, Code, Minus
} from 'lucide-react';
import './SlashCommandMenu.css';

const iconMap = {
  heading1: Heading1,
  heading2: Heading2,
  heading3: Heading3,
  list: List,
  listOrdered: ListOrdered,
  checkSquare: CheckSquare,
  quote: Quote,
  code: Code,
  minus: Minus,
};

/**
 * SlashCommandMenu - Floating command palette for slash commands
 * Renders as a glass-styled dropdown menu near the cursor
 */
const SlashCommandMenu = forwardRef(({ items, command }, ref) => {
  const [selectedIndex, setSelectedIndex] = useState(0);

  const selectItem = useCallback((index) => {
    const item = items[index];
    if (item) {
      command(item);
    }
  }, [items, command]);

  const upHandler = useCallback(() => {
    setSelectedIndex((prev) => (prev - 1 + items.length) % items.length);
  }, [items.length]);

  const downHandler = useCallback(() => {
    setSelectedIndex((prev) => (prev + 1) % items.length);
  }, [items.length]);

  const enterHandler = useCallback(() => {
    selectItem(selectedIndex);
  }, [selectItem, selectedIndex]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [items]);

  useImperativeHandle(ref, () => ({
    onKeyDown: ({ event }) => {
      if (event.key === 'ArrowUp') {
        upHandler();
        return true;
      }
      if (event.key === 'ArrowDown') {
        downHandler();
        return true;
      }
      if (event.key === 'Enter') {
        enterHandler();
        return true;
      }
      return false;
    },
  }), [upHandler, downHandler, enterHandler]);

  if (!items.length) {
    return (
      <div className="slash-command-menu">
        <div className="slash-command-empty">No commands found</div>
      </div>
    );
  }

  return (
    <div className="slash-command-menu">
      <div className="slash-command-header">
        <span>Type to filter...</span>
        <span className="slash-command-hint">
          <kbd>↑</kbd><kbd>↓</kbd> navigate <kbd>↵</kbd> select
        </span>
      </div>
      <div className="slash-command-list">
        {items.map((item, index) => {
          const IconComponent = iconMap[item.icon] || List;
          return (
            <button
              key={item.title}
              className={`slash-command-item ${index === selectedIndex ? 'selected' : ''}`}
              onClick={() => selectItem(index)}
              onMouseEnter={() => setSelectedIndex(index)}
            >
              <div className="slash-command-icon">
                <IconComponent size={18} />
              </div>
              <div className="slash-command-content">
                <span className="slash-command-title">{item.title}</span>
                <span className="slash-command-description">{item.description}</span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
});

SlashCommandMenu.displayName = 'SlashCommandMenu';

export default SlashCommandMenu;
