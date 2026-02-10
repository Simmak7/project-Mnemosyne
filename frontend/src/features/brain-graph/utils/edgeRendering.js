/**
 * edgeRendering.js - Canvas edge drawing utilities
 *
 * Provides color schemes and rendering functions for graph edges.
 * Different styles for wikilinks, tags, semantic connections.
 * Supports light/dark theme switching.
 */

// Edge color mapping based on type - DARK MODE (default)
export const EDGE_COLORS_DARK = {
  wikilink: {
    base: 'rgba(255, 255, 255, 0.6)',
    highlight: 'rgba(255, 255, 255, 0.9)',
    glow: 'rgba(255, 255, 255, 0.3)',
  },
  tag: {
    base: 'rgba(52, 211, 153, 0.5)', // Emerald
    highlight: 'rgba(52, 211, 153, 0.8)',
    glow: 'rgba(52, 211, 153, 0.2)',
  },
  image: {
    base: 'rgba(34, 211, 238, 0.5)', // Cyan for image connections
    highlight: 'rgba(34, 211, 238, 0.8)',
    glow: 'rgba(34, 211, 238, 0.2)',
  },
  source: {
    base: 'rgba(251, 113, 133, 0.5)', // Rose for document sources
    highlight: 'rgba(251, 113, 133, 0.8)',
    glow: 'rgba(251, 113, 133, 0.2)',
  },
  semantic: {
    base: 'rgba(129, 140, 248, 0.4)', // Violet
    highlight: 'rgba(129, 140, 248, 0.7)',
    glow: 'rgba(129, 140, 248, 0.2)',
  },
  mentions: {
    base: 'rgba(129, 140, 248, 0.3)', // Violet lighter
    highlight: 'rgba(129, 140, 248, 0.6)',
    glow: 'rgba(129, 140, 248, 0.15)',
  },
  session: {
    base: 'rgba(156, 163, 175, 0.3)', // Gray
    highlight: 'rgba(156, 163, 175, 0.6)',
    glow: 'rgba(156, 163, 175, 0.15)',
  },
  default: {
    base: 'rgba(156, 163, 175, 0.4)',
    highlight: 'rgba(156, 163, 175, 0.7)',
    glow: 'rgba(156, 163, 175, 0.2)',
  },
};

// Edge color mapping - LIGHT MODE
export const EDGE_COLORS_LIGHT = {
  wikilink: {
    base: 'rgba(100, 116, 139, 0.6)', // Slate-500
    highlight: 'rgba(71, 85, 105, 0.9)', // Slate-600
    glow: 'rgba(100, 116, 139, 0.3)',
  },
  tag: {
    base: 'rgba(5, 150, 105, 0.6)', // Emerald-600
    highlight: 'rgba(4, 120, 87, 0.8)', // Emerald-700
    glow: 'rgba(5, 150, 105, 0.2)',
  },
  image: {
    base: 'rgba(8, 145, 178, 0.6)', // Cyan-600
    highlight: 'rgba(14, 116, 144, 0.8)', // Cyan-700
    glow: 'rgba(8, 145, 178, 0.2)',
  },
  source: {
    base: 'rgba(225, 29, 72, 0.6)', // Rose-600
    highlight: 'rgba(190, 18, 60, 0.8)', // Rose-700
    glow: 'rgba(225, 29, 72, 0.2)',
  },
  semantic: {
    base: 'rgba(99, 102, 241, 0.5)', // Indigo-500
    highlight: 'rgba(79, 70, 229, 0.7)', // Indigo-600
    glow: 'rgba(99, 102, 241, 0.2)',
  },
  mentions: {
    base: 'rgba(99, 102, 241, 0.4)', // Indigo-500 lighter
    highlight: 'rgba(79, 70, 229, 0.6)', // Indigo-600
    glow: 'rgba(99, 102, 241, 0.15)',
  },
  session: {
    base: 'rgba(107, 114, 128, 0.4)', // Gray-500
    highlight: 'rgba(75, 85, 99, 0.6)', // Gray-600
    glow: 'rgba(107, 114, 128, 0.15)',
  },
  default: {
    base: 'rgba(107, 114, 128, 0.5)',
    highlight: 'rgba(75, 85, 99, 0.7)',
    glow: 'rgba(107, 114, 128, 0.2)',
  },
};

// Default to dark mode colors for backward compatibility
export const EDGE_COLORS = EDGE_COLORS_DARK;

/**
 * Check if light theme is active
 */
export function isLightTheme() {
  if (typeof document === 'undefined') return false;
  return document.documentElement.getAttribute('data-theme') === 'light';
}

/**
 * Get edge colors based on current theme.
 * Pass isLight to avoid per-edge DOM reads.
 */
export function getThemedEdgeColors(isLight) {
  if (isLight === undefined) isLight = isLightTheme();
  return isLight ? EDGE_COLORS_LIGHT : EDGE_COLORS_DARK;
}

// Dash patterns for different edge types
export const EDGE_DASH_PATTERNS = {
  wikilink: [], // Solid line
  tag: [5, 3], // Dashed
  image: [3, 3], // Short dash for image connections
  source: [], // Solid line for document sources
  semantic: [2, 2], // Dotted
  mentions: [8, 4, 2, 4], // Dash-dot
  session: [4, 8], // Sparse dash
  default: [],
};

/**
 * Get color scheme for an edge based on its type and current theme
 */
export function getEdgeColor(edge, isLight) {
  const type = edge?.type || 'default';
  const colors = getThemedEdgeColors(isLight);
  return colors[type] || colors.default;
}

/**
 * Get dash pattern for edge type
 */
export function getEdgeDash(edge) {
  const type = edge?.type || 'default';
  return EDGE_DASH_PATTERNS[type] || EDGE_DASH_PATTERNS.default;
}

/**
 * Calculate edge width based on weight
 */
export function getEdgeWidth(edge, { minWidth = 0.5, maxWidth = 4, baseWidth = 1 } = {}) {
  const weight = edge.weight ?? 0.5;
  const width = baseWidth + weight * 2;
  return Math.min(Math.max(width, minWidth), maxWidth);
}

/**
 * Render an edge on canvas context
 */
export function renderEdge(ctx, edge, start, end, state = {}) {
  const { isSelected, isHighlighted, globalScale = 1 } = state;
  const colors = getEdgeColor(edge);
  const dash = getEdgeDash(edge);
  const width = getEdgeWidth(edge);

  ctx.save();

  // Draw glow for selected/highlighted edges
  if (isSelected || isHighlighted) {
    ctx.beginPath();
    ctx.moveTo(start.x, start.y);
    ctx.lineTo(end.x, end.y);
    ctx.strokeStyle = colors.glow;
    ctx.lineWidth = width + 6;
    ctx.stroke();
  }

  // Draw edge line
  ctx.beginPath();
  ctx.moveTo(start.x, start.y);
  ctx.lineTo(end.x, end.y);
  ctx.strokeStyle = isSelected || isHighlighted ? colors.highlight : colors.base;
  ctx.lineWidth = isSelected ? width + 1 : width;
  ctx.setLineDash(dash);
  ctx.stroke();

  ctx.restore();
}

/**
 * Render edge with arrow (for directed edges)
 */
export function renderDirectedEdge(ctx, edge, start, end, state = {}) {
  const { globalScale = 1 } = state;
  const width = getEdgeWidth(edge);

  // First render the line
  renderEdge(ctx, edge, start, end, state);

  // Calculate arrow position (near target)
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  const len = Math.sqrt(dx * dx + dy * dy);

  if (len < 20) return; // Skip arrow for very short edges

  const arrowSize = Math.max(4, 6 / globalScale);
  const nodeRadius = 8; // Approximate node radius

  // Position arrow at edge of target node
  const ratio = (len - nodeRadius - arrowSize) / len;
  const arrowX = start.x + dx * ratio;
  const arrowY = start.y + dy * ratio;

  // Calculate arrow angle
  const angle = Math.atan2(dy, dx);

  // Draw arrow
  ctx.save();
  ctx.translate(arrowX, arrowY);
  ctx.rotate(angle);

  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(-arrowSize, arrowSize / 2);
  ctx.lineTo(-arrowSize, -arrowSize / 2);
  ctx.closePath();

  ctx.fillStyle = getEdgeColor(edge).base;
  ctx.fill();

  ctx.restore();
}

/**
 * Render curved edge (for self-loops or bundled edges)
 */
export function renderCurvedEdge(ctx, edge, start, end, curvature = 0.3, state = {}) {
  const colors = getEdgeColor(edge);
  const width = getEdgeWidth(edge);
  const { isSelected, isHighlighted } = state;

  // Calculate control point
  const midX = (start.x + end.x) / 2;
  const midY = (start.y + end.y) / 2;

  // Perpendicular offset for curve
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  const perpX = -dy * curvature;
  const perpY = dx * curvature;

  const ctrlX = midX + perpX;
  const ctrlY = midY + perpY;

  ctx.save();

  // Draw glow
  if (isSelected || isHighlighted) {
    ctx.beginPath();
    ctx.moveTo(start.x, start.y);
    ctx.quadraticCurveTo(ctrlX, ctrlY, end.x, end.y);
    ctx.strokeStyle = colors.glow;
    ctx.lineWidth = width + 6;
    ctx.stroke();
  }

  // Draw curve
  ctx.beginPath();
  ctx.moveTo(start.x, start.y);
  ctx.quadraticCurveTo(ctrlX, ctrlY, end.x, end.y);
  ctx.strokeStyle = isSelected || isHighlighted ? colors.highlight : colors.base;
  ctx.lineWidth = isSelected ? width + 1 : width;
  ctx.setLineDash(getEdgeDash(edge));
  ctx.stroke();

  ctx.restore();
}

/**
 * Get edge label for display
 */
export function getEdgeLabel(edge) {
  const labels = {
    wikilink: 'links to',
    tag: 'tagged',
    source: 'source',
    semantic: `${Math.round((edge.weight || 0) * 100)}% similar`,
    mentions: 'mentions',
    session: 'same session',
  };

  return labels[edge.type] || edge.type;
}
