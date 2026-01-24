/**
 * useGraphLayout - Force simulation configuration
 *
 * Provides layout presets and controls for force-directed graph.
 * Manages zoom, pan, and physics settings.
 */

import { useState, useCallback, useRef, useMemo } from 'react';

// Layout preset configurations (synced with layoutPresets.js)
// Key differences: tight < explore < map < cluster (increasing spread)
export const LAYOUT_PRESETS = {
  tight: {
    name: 'Tight',
    description: 'Dense, minimal spacing',
    physics: {
      charge: -40,            // Very low repulsion - nodes stay close
      linkDistance: 25,       // Very short links
      linkStrength: 0.95,     // Very strong links
      centerStrength: 0.2,    // Strong center pull
      velocityDecay: 0.6,
      alphaDecay: 0.035,
    },
  },
  explore: {
    name: 'Explore',
    description: 'Compact layout for local navigation',
    physics: {
      charge: -80,            // Moderate repulsion
      linkDistance: 50,       // Short links
      linkStrength: 0.8,      // Strong links
      centerStrength: 0.15,   // Good center pull
      velocityDecay: 0.5,
      alphaDecay: 0.03,
    },
  },
  map: {
    name: 'Map',
    description: 'Spread layout for overview',
    physics: {
      charge: -200,           // High repulsion - nodes spread out
      linkDistance: 120,      // Long links
      linkStrength: 0.4,      // Weaker links allow spreading
      centerStrength: 0.08,   // Light center pull
      velocityDecay: 0.4,
      alphaDecay: 0.02,
    },
  },
  cluster: {
    name: 'Cluster',
    description: 'Maximum spread for structure',
    physics: {
      charge: -350,           // Very high repulsion - maximum spread
      linkDistance: 150,      // Very long links
      linkStrength: 0.3,      // Weak links for freedom
      centerStrength: 0.05,   // Minimal center pull
      velocityDecay: 0.35,
      alphaDecay: 0.015,
    },
  },
};

// Default zoom limits
const ZOOM_LIMITS = { min: 0.1, max: 5 };

/**
 * Graph layout configuration hook
 */
export function useGraphLayout(initialPreset = 'explore') {
  const [preset, setPreset] = useState(initialPreset);
  const [zoom, setZoom] = useState(1);
  const [center, setCenter] = useState({ x: 0, y: 0 });
  const [isPaused, setIsPaused] = useState(false);
  const [edgeBundling, setEdgeBundling] = useState(false);

  // Ref to force graph instance
  const graphRef = useRef(null);

  // Get current physics config
  const physics = useMemo(() => {
    return LAYOUT_PRESETS[preset]?.physics || LAYOUT_PRESETS.explore.physics;
  }, [preset]);

  // Change layout preset
  const changePreset = useCallback((newPreset) => {
    if (LAYOUT_PRESETS[newPreset]) {
      setPreset(newPreset);
      // Restart simulation with new config
      if (graphRef.current) {
        graphRef.current.d3ReheatSimulation?.();
      }
    }
  }, []);

  // Zoom in
  const zoomIn = useCallback(() => {
    setZoom((prev) => {
      const newZoom = Math.min(prev * 1.2, ZOOM_LIMITS.max);
      // Apply zoom to graph canvas
      if (graphRef.current) {
        graphRef.current.zoom?.(newZoom, 300);
      }
      return newZoom;
    });
  }, []);

  // Zoom out
  const zoomOut = useCallback(() => {
    setZoom((prev) => {
      const newZoom = Math.max(prev / 1.2, ZOOM_LIMITS.min);
      // Apply zoom to graph canvas
      if (graphRef.current) {
        graphRef.current.zoom?.(newZoom, 300);
      }
      return newZoom;
    });
  }, []);

  // Reset zoom
  const resetZoom = useCallback(() => {
    setZoom(1);
    setCenter({ x: 0, y: 0 });
    if (graphRef.current) {
      graphRef.current.centerAt?.(0, 0, 500);
      graphRef.current.zoom?.(1, 500);
    }
  }, []);

  // Fit graph to view
  const fitToView = useCallback((padding = 50) => {
    if (graphRef.current) {
      graphRef.current.zoomToFit?.(500, padding);
    }
  }, []);

  // Center on a specific node
  const centerOnNode = useCallback((nodeId) => {
    if (graphRef.current) {
      const node = graphRef.current.graphData?.().nodes.find((n) => n.id === nodeId);
      if (node) {
        graphRef.current.centerAt?.(node.x, node.y, 500);
        graphRef.current.zoom?.(2, 500);
      }
    }
  }, []);

  // Toggle simulation pause
  const togglePause = useCallback(() => {
    setIsPaused((prev) => {
      const next = !prev;
      if (graphRef.current) {
        if (next) {
          graphRef.current.pauseAnimation?.();
        } else {
          graphRef.current.resumeAnimation?.();
        }
      }
      return next;
    });
  }, []);

  // Reheat simulation (shake things up)
  const reheat = useCallback(() => {
    if (graphRef.current) {
      graphRef.current.d3ReheatSimulation?.();
    }
  }, []);

  // Toggle edge bundling (uses curved links for approximation)
  const toggleEdgeBundling = useCallback(() => {
    setEdgeBundling((prev) => !prev);
  }, []);

  // Pan by offset
  const pan = useCallback((dx, dy) => {
    setCenter((prev) => ({ x: prev.x + dx, y: prev.y + dy }));
    // Note: actual panning is handled by react-force-graph internally
  }, []);

  // Keyboard zoom/pan handler
  const handleLayoutKeyDown = useCallback((event) => {
    const PAN_STEP = 50;

    switch (event.key) {
      case '+':
      case '=':
        zoomIn();
        break;
      case '-':
      case '_':
        zoomOut();
        break;
      case '0':
        resetZoom();
        break;
      case 'ArrowUp':
        pan(0, -PAN_STEP);
        break;
      case 'ArrowDown':
        pan(0, PAN_STEP);
        break;
      case 'ArrowLeft':
        pan(-PAN_STEP, 0);
        break;
      case 'ArrowRight':
        pan(PAN_STEP, 0);
        break;
      case ' ':
        event.preventDefault();
        togglePause();
        break;
      default:
        break;
    }
  }, [zoomIn, zoomOut, resetZoom, pan, togglePause]);

  return {
    // State
    preset,
    physics,
    zoom,
    center,
    isPaused,
    edgeBundling,
    graphRef,

    // Preset actions
    changePreset,
    presets: LAYOUT_PRESETS,

    // Zoom actions
    zoomIn,
    zoomOut,
    resetZoom,
    setZoom,

    // View actions
    fitToView,
    centerOnNode,
    pan,

    // Simulation actions
    togglePause,
    reheat,
    toggleEdgeBundling,

    // Event handlers
    handleLayoutKeyDown,
  };
}

export default useGraphLayout;
