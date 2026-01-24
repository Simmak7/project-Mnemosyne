/**
 * layoutPresets.js - Graph layout configurations
 *
 * Provides preset configurations for different graph views.
 * Used by react-force-graph for physics simulation.
 */

/**
 * Layout preset definitions
 *
 * Key differences:
 * - tight: Dense, minimal spacing (nodes very close)
 * - explore: Compact for navigation (default)
 * - map: Spread for overview (medium spacing)
 * - cluster: Maximum spread for seeing structure
 */
export const LAYOUT_PRESETS = {
  tight: {
    id: 'tight',
    name: 'Tight',
    description: 'Dense, compact spacing',
    icon: 'minimize',
    physics: {
      chargeStrength: -200,       // Similar to old Map - good spacing
      linkDistance: 120,          // Medium links
      linkStrength: 0.5,          // Moderate links
      centerStrength: 0.12,       // Good center pull
      velocityDecay: 0.5,
      alphaDecay: 0.025,
      alphaMin: 0.001,
    },
    display: {
      showLabels: 'hover',
      nodeScale: 0.9,
      edgeOpacity: 0.6,
      curvedEdges: false,
    },
  },

  explore: {
    id: 'explore',
    name: 'Explore',
    description: 'Spread layout for navigation',
    icon: 'compass',
    physics: {
      chargeStrength: -350,       // Similar to old Cluster - well spread
      linkDistance: 150,          // Long links
      linkStrength: 0.35,         // Moderate-weak links for spreading
      centerStrength: 0.08,       // Light center pull
      velocityDecay: 0.4,
      alphaDecay: 0.02,
      alphaMin: 0.001,
    },
    display: {
      showLabels: 'hover',
      nodeScale: 1.0,
      edgeOpacity: 0.5,
      curvedEdges: false,
    },
  },

  map: {
    id: 'map',
    name: 'Map',
    description: 'Wide layout for overview',
    icon: 'map',
    physics: {
      chargeStrength: -500,       // High repulsion - nodes spread wide
      linkDistance: 200,          // Very long links
      linkStrength: 0.25,         // Weak links for maximum spreading
      centerStrength: 0.05,       // Minimal center pull
      velocityDecay: 0.35,
      alphaDecay: 0.015,
      alphaMin: 0.001,
    },
    display: {
      showLabels: 'none',
      nodeScale: 0.8,
      edgeOpacity: 0.4,
      curvedEdges: false,
    },
  },

  cluster: {
    id: 'cluster',
    name: 'Cluster',
    description: 'Maximum spread for structure',
    icon: 'layers',
    physics: {
      chargeStrength: -700,       // Very high repulsion - maximum spread
      linkDistance: 250,          // Very long links
      linkStrength: 0.2,          // Very weak links for freedom
      centerStrength: 0.03,       // Very minimal center pull
      velocityDecay: 0.3,
      alphaDecay: 0.012,
      alphaMin: 0.001,
    },
    display: {
      showLabels: 'hover',
      nodeScale: 1.0,
      edgeOpacity: 0.5,
      curvedEdges: true,
    },
  },
};

/**
 * Get layout configuration by ID
 */
export function getLayoutConfig(presetId) {
  return LAYOUT_PRESETS[presetId] || LAYOUT_PRESETS.explore;
}

/**
 * Get all available layout presets
 */
export function getAllPresets() {
  return Object.values(LAYOUT_PRESETS);
}

/**
 * Build D3 force configuration from preset
 */
export function buildForceConfig(presetId) {
  const preset = getLayoutConfig(presetId);
  const { physics } = preset;

  return {
    charge: () => physics.chargeStrength,
    link: {
      distance: physics.linkDistance,
      strength: physics.linkStrength,
    },
    center: {
      strength: physics.centerStrength,
    },
    velocityDecay: physics.velocityDecay,
    alphaDecay: physics.alphaDecay,
    alphaMin: physics.alphaMin,
  };
}

/**
 * LOD (Level of Detail) thresholds for zoom levels
 */
export const LOD_THRESHOLDS = {
  HIGH: 2.0,   // Zoom > 2.0: show all nodes + labels
  MEDIUM: 1.0, // 1.0 - 2.0: show nodes, minimal labels
  LOW: 0.5,    // < 0.5: show cluster meta-nodes only
};

/**
 * Get LOD level from zoom
 */
export function getLODLevel(zoom) {
  if (zoom >= LOD_THRESHOLDS.HIGH) return 'high';
  if (zoom >= LOD_THRESHOLDS.MEDIUM) return 'medium';
  return 'low';
}

/**
 * Get display settings for LOD level
 */
export function getLODSettings(zoom) {
  const level = getLODLevel(zoom);

  return {
    showAllLabels: level === 'high',
    showHubLabels: level !== 'low',
    nodeMinSize: level === 'low' ? 2 : 4,
    edgeMinWidth: level === 'low' ? 0.3 : 0.5,
    renderEdges: level !== 'low' || zoom > 0.3,
  };
}

/**
 * Animation duration constants
 */
export const ANIMATION_DURATIONS = {
  fast: 200,
  normal: 500,
  slow: 1000,
  pan: 300,
  zoom: 400,
  focus: 600,
};

export default LAYOUT_PRESETS;
