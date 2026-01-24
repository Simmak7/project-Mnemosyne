import React from 'react';
import './GlassPanel.css';

/**
 * GlassPanel - Reusable glassmorphism container component
 *
 * Variants:
 * - default: Standard glass panel with backdrop blur
 * - elevated: Floating panel with stronger shadow (modals, dropdowns)
 * - inset: Recessed panel for input fields
 * - interactive: Clickable glass panel with hover states
 *
 * Semantic variants (with accent colors):
 * - ai: Violet tinted for AI-related content
 * - image: Cyan tinted for image content
 * - note: Amber tinted for note content
 * - link: Emerald tinted for connections
 */
function GlassPanel({
  children,
  variant = 'default',
  className = '',
  padding = 'md',
  as: Component = 'div',
  onClick,
  ...props
}) {
  const paddingClass = padding ? `ng-panel-p-${padding}` : '';
  const isInteractive = variant === 'interactive' || onClick;

  const variantClass = {
    default: 'ng-glass',
    elevated: 'ng-glass-elevated',
    inset: 'ng-glass-inset',
    interactive: 'ng-glass-interactive',
    light: 'ng-glass-light',
    heavy: 'ng-glass-heavy',
    ai: 'ng-glass-ai',
    image: 'ng-glass-image',
    note: 'ng-glass-note',
    link: 'ng-glass-link',
  }[variant] || 'ng-glass';

  return (
    <Component
      className={`glass-panel ${variantClass} ${paddingClass} ${className} ${isInteractive ? 'ng-transition-interactive' : ''}`}
      onClick={onClick}
      role={isInteractive ? 'button' : undefined}
      tabIndex={isInteractive ? 0 : undefined}
      onKeyDown={isInteractive ? (e) => e.key === 'Enter' && onClick?.(e) : undefined}
      {...props}
    >
      {children}
    </Component>
  );
}

export default GlassPanel;
