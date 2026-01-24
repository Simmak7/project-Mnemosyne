import React, { forwardRef, useEffect, useImperativeHandle, useState } from 'react';
import './SuggestionList.css';

/**
 * SuggestionList - Dropdown UI for wikilink and hashtag autocomplete
 * Supports keyboard navigation (Arrow keys + Enter)
 */
export const SuggestionList = forwardRef((props, ref) => {
  const [selectedIndex, setSelectedIndex] = useState(0);

  const selectItem = index => {
    const item = props.items[index];

    if (item) {
      props.command(item);
    }
  };

  const upHandler = () => {
    setSelectedIndex((selectedIndex + props.items.length - 1) % props.items.length);
  };

  const downHandler = () => {
    setSelectedIndex((selectedIndex + 1) % props.items.length);
  };

  const enterHandler = () => {
    selectItem(selectedIndex);
  };

  useEffect(() => setSelectedIndex(0), [props.items]);

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
  }));

  if (props.items.length === 0) {
    return (
      <div className="suggestion-list">
        <div className="suggestion-item-empty">
          {props.isHashtag ? 'No tags found' : 'No notes found'}
        </div>
      </div>
    );
  }

  return (
    <div className="suggestion-list">
      {props.items.map((item, index) => {
        const displayText = props.isHashtag ? item.name : item.title;
        const prefix = props.isHashtag ? '#' : '[[';
        const suffix = props.isHashtag ? '' : ']]';

        return (
          <button
            className={`suggestion-item ${index === selectedIndex ? 'selected' : ''} ${
              props.isHashtag ? 'hashtag' : 'wikilink'
            }`}
            key={index}
            onClick={() => selectItem(index)}
            onMouseEnter={() => setSelectedIndex(index)}
          >
            <span className="suggestion-prefix">{prefix}</span>
            <span className="suggestion-text">{displayText}</span>
            <span className="suggestion-suffix">{suffix}</span>
          </button>
        );
      })}
    </div>
  );
});

SuggestionList.displayName = 'SuggestionList';
