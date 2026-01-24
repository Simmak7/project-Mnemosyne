import React, { useState, useCallback, useEffect } from 'react';
import { Menu, X, ChevronLeft, ChevronRight } from 'lucide-react';
import './FloatingSidebar.css';

/**
 * FloatingSidebar - Collapsible overlay sidebar with glass effect
 *
 * Features:
 * - Floats over content (doesn't push)
 * - Collapses to icon rail
 * - Keyboard shortcut support (Ctrl+\)
 * - Smooth expand/collapse animations
 * - Glass morphism styling
 */
function FloatingSidebar({
  children,
  position = 'left',
  defaultCollapsed = false,
  collapsedWidth = 64,
  expandedWidth = 280,
  onCollapsedChange,
  className = '',
  header,
  footer,
}) {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);
  const [isHovering, setIsHovering] = useState(false);

  // Handle keyboard shortcut (Ctrl+\)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.ctrlKey && e.key === '\\') {
        e.preventDefault();
        toggleCollapsed();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const toggleCollapsed = useCallback(() => {
    setIsCollapsed((prev) => {
      const newState = !prev;
      onCollapsedChange?.(newState);
      return newState;
    });
  }, [onCollapsedChange]);

  const handleMouseEnter = () => {
    if (isCollapsed) {
      setIsHovering(true);
    }
  };

  const handleMouseLeave = () => {
    setIsHovering(false);
  };

  // Determine if sidebar should show expanded content
  const showExpanded = !isCollapsed || isHovering;

  return (
    <aside
      className={`floating-sidebar ${position} ${isCollapsed ? 'collapsed' : 'expanded'} ${isHovering ? 'hover-expanded' : ''} ${className}`}
      style={{
        '--sidebar-width': showExpanded ? `${expandedWidth}px` : `${collapsedWidth}px`,
        '--sidebar-collapsed-width': `${collapsedWidth}px`,
        '--sidebar-expanded-width': `${expandedWidth}px`,
      }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      role="navigation"
      aria-label="Main navigation"
      aria-expanded={!isCollapsed}
    >
      {/* Glass background layer */}
      <div className="sidebar-glass-bg" />

      {/* Toggle button */}
      <button
        className="sidebar-toggle ng-glass-interactive"
        onClick={toggleCollapsed}
        aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        title={isCollapsed ? 'Expand (Ctrl+\\)' : 'Collapse (Ctrl+\\)'}
      >
        {isCollapsed ? (
          <ChevronRight size={16} />
        ) : (
          <ChevronLeft size={16} />
        )}
      </button>

      {/* Header section */}
      {header && (
        <div className={`sidebar-header ${showExpanded ? 'show-full' : 'show-icon'}`}>
          {header}
        </div>
      )}

      {/* Main content */}
      <div className="sidebar-content ng-scrollbar">
        <div className={`sidebar-content-inner ${showExpanded ? 'expanded' : 'collapsed'}`}>
          {children}
        </div>
      </div>

      {/* Footer section */}
      {footer && (
        <div className={`sidebar-footer ${showExpanded ? 'show-full' : 'show-icon'}`}>
          {footer}
        </div>
      )}
    </aside>
  );
}

export default FloatingSidebar;
