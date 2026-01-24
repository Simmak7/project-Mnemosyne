import React from 'react';
import { GripVertical } from 'lucide-react';
import './GlassResizeHandle.css';

/**
 * GlassResizeHandle - Glass-styled resize handle for panels
 *
 * Designed to work with react-resizable-panels or similar libraries.
 * Provides visual feedback and glass morphism styling.
 */
function GlassResizeHandle({
  direction = 'horizontal',
  className = '',
  showGrip = false,
  ...props
}) {
  const isHorizontal = direction === 'horizontal';

  return (
    <div
      className={`glass-resize-handle ${direction} ${className}`}
      role="separator"
      aria-orientation={isHorizontal ? 'vertical' : 'horizontal'}
      {...props}
    >
      {/* Glow indicator on hover */}
      <div className="resize-handle-glow" />

      {/* Visual grip indicator */}
      {showGrip && (
        <div className="resize-handle-grip">
          {isHorizontal ? (
            <GripVertical size={12} />
          ) : (
            <GripVertical size={12} style={{ transform: 'rotate(90deg)' }} />
          )}
        </div>
      )}
    </div>
  );
}

export default GlassResizeHandle;
