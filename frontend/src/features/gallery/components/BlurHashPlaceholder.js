import React, { useMemo } from 'react';
import { Blurhash } from 'react-blurhash';
import './BlurHashPlaceholder.css';

/**
 * BlurHashPlaceholder - Renders a blur hash as an instant loading placeholder
 *
 * Props:
 * - hash: BlurHash string (e.g., "LEHV6nWB2yk8pyo0adR*.7kCMdnj")
 * - width: Container width in pixels
 * - height: Container height in pixels
 * - className: Optional additional CSS classes
 *
 * Falls back to shimmer effect if no hash is provided
 */
function BlurHashPlaceholder({ hash, width, height, className = '' }) {
  // Calculate resolution multiplier for crisp rendering
  const resolutionX = useMemo(() => Math.min(32, Math.ceil(width / 10)), [width]);
  const resolutionY = useMemo(() => Math.min(32, Math.ceil(height / 10)), [height]);

  // If no hash, show shimmer fallback
  if (!hash) {
    return (
      <div
        className={`blurhash-placeholder shimmer ${className}`}
        style={{ width, height }}
      >
        <div className="shimmer-effect" />
      </div>
    );
  }

  return (
    <div
      className={`blurhash-placeholder ${className}`}
      style={{ width, height }}
    >
      <Blurhash
        hash={hash}
        width={width}
        height={height}
        resolutionX={resolutionX}
        resolutionY={resolutionY}
        punch={1}
      />
    </div>
  );
}

export default React.memo(BlurHashPlaceholder);
