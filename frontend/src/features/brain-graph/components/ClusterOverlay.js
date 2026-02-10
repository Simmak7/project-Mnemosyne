/**
 * ClusterOverlay - Floating community labels on the graph canvas
 *
 * Renders positioned HTML labels at each cluster's centroid.
 * Uses graph2ScreenCoords to project world coords to screen.
 * Re-positions on animation frame for smooth following.
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import './ClusterOverlay.css';

export function ClusterOverlay({ centroids, graphRef }) {
  const [screenPositions, setScreenPositions] = useState([]);
  const rafRef = useRef(null);

  // Convert world coordinates to screen coordinates
  const updatePositions = useCallback(() => {
    const graph = graphRef?.current;
    if (!graph || !centroids?.length) {
      setScreenPositions([]);
      return;
    }

    const canvasW = graph.width?.() || 800;
    const canvasH = graph.height?.() || 600;

    const positions = centroids
      .filter((c) => c.x !== 0 || c.y !== 0) // Skip unpositioned centroids
      .map((c) => {
        const screen = graph.graph2ScreenCoords(c.x, c.y);
        if (!screen) return null;
        // Only show if on-screen (with margin)
        if (screen.x < -50 || screen.x > canvasW + 50 || screen.y < -50 || screen.y > canvasH + 50) return null;
        return { ...c, sx: screen.x, sy: screen.y };
      })
      .filter(Boolean);

    setScreenPositions(positions);
    rafRef.current = requestAnimationFrame(updatePositions);
  }, [centroids, graphRef]);

  useEffect(() => {
    rafRef.current = requestAnimationFrame(updatePositions);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [updatePositions]);

  if (!screenPositions.length) return null;

  return (
    <div className="cluster-overlay">
      {screenPositions.map((c) => (
        <div
          key={c.id}
          className="cluster-overlay__label"
          style={{
            left: `${c.sx}px`,
            top: `${c.sy}px`,
          }}
        >
          <span
            className="cluster-overlay__dot"
            style={{ backgroundColor: c.color }}
          />
          <span className="cluster-overlay__text">{c.label}</span>
        </div>
      ))}
    </div>
  );
}

export default ClusterOverlay;
