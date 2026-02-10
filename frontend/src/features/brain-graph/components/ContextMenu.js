/**
 * ContextMenu - Right-click context menu for graph nodes
 *
 * Shows Focus/Expand/Open/Pin/Find Path actions at cursor position.
 * Auto-closes on click-away or action selection.
 */

import React, { useEffect, useRef, useCallback } from 'react';
import { Crosshair, Maximize2, ExternalLink, Pin, GitBranch } from 'lucide-react';

import './ContextMenu.css';

export function ContextMenu({ menu, graphState, onViewChange }) {
  const ref = useRef(null);

  // Close on click-away or Escape
  useEffect(() => {
    if (!menu) return;
    const handleClose = (e) => {
      if (ref.current && !ref.current.contains(e.target)) graphState.setContextMenu(null);
    };
    const handleKey = (e) => {
      if (e.key === 'Escape') graphState.setContextMenu(null);
    };
    document.addEventListener('mousedown', handleClose);
    document.addEventListener('keydown', handleKey);
    return () => {
      document.removeEventListener('mousedown', handleClose);
      document.removeEventListener('keydown', handleKey);
    };
  }, [menu, graphState]);

  // Clamp position so menu doesn't overflow viewport
  const getPosition = useCallback(() => {
    if (!menu) return {};
    const pad = 8;
    const w = 180, h = 200;
    const x = Math.min(menu.x, window.innerWidth - w - pad);
    const y = Math.min(menu.y, window.innerHeight - h - pad);
    return { left: `${Math.max(pad, x)}px`, top: `${Math.max(pad, y)}px` };
  }, [menu]);

  if (!menu) return null;

  const { node } = menu;
  const isPinned = graphState.isPinned(node.id);
  const title = node.title || node.id;

  const actions = [
    {
      label: 'Focus Here',
      icon: Crosshair,
      handler: () => graphState.setFocus(node.id),
    },
    {
      label: 'Expand',
      icon: Maximize2,
      handler: () => { graphState.handleNodeClick(node, {}); graphState.expandSelected(); },
    },
    {
      label: 'Open',
      icon: ExternalLink,
      handler: () => graphState.handleNodeDoubleClick(node),
    },
    {
      label: isPinned ? 'Unpin' : 'Pin',
      icon: Pin,
      handler: () => graphState.togglePin(node.id),
    },
    {
      label: 'Find Path From',
      icon: GitBranch,
      handler: () => {
        graphState.setPathSource(node.id);
        if (onViewChange) onViewChange('pathfinder');
      },
    },
  ];

  return (
    <div className="graph-context-menu" ref={ref} style={getPosition()}>
      <div className="graph-context-menu__title">{title}</div>
      {actions.map((action) => (
        <button
          key={action.label}
          className="graph-context-menu__item"
          onClick={() => { action.handler(); graphState.setContextMenu(null); }}
        >
          <action.icon size={14} />
          {action.label}
        </button>
      ))}
    </div>
  );
}

export default ContextMenu;
