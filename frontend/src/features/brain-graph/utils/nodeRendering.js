/**
 * nodeRendering.js - Canvas node drawing utilities
 *
 * Provides color schemes and rendering functions for graph nodes.
 * Uses Neural Glass semantic colors.
 * Supports light/dark theme switching.
 */

/**
 * Check if light theme is active
 */
export function isLightTheme() {
  if (typeof document === 'undefined') return false;
  return document.documentElement.getAttribute('data-theme') === 'light';
}

// Node color mapping based on type
export const NODE_COLORS = {
  note: {
    base: '#fbbf24', // Amber
    glow: 'rgba(251, 191, 36, 0.3)',
    border: 'rgba(251, 191, 36, 0.6)',
  },
  tag: {
    base: '#34d399', // Emerald
    glow: 'rgba(52, 211, 153, 0.3)',
    border: 'rgba(52, 211, 153, 0.6)',
  },
  image: {
    base: '#22d3ee', // Cyan
    glow: 'rgba(34, 211, 238, 0.3)',
    border: 'rgba(34, 211, 238, 0.6)',
  },
  media: {
    base: '#22d3ee', // Cyan (alias for image)
    glow: 'rgba(34, 211, 238, 0.3)',
    border: 'rgba(34, 211, 238, 0.6)',
  },
  entity: {
    base: '#818cf8', // Violet
    glow: 'rgba(129, 140, 248, 0.3)',
    border: 'rgba(129, 140, 248, 0.6)',
  },
  collection: {
    base: '#f472b6', // Pink
    glow: 'rgba(244, 114, 182, 0.3)',
    border: 'rgba(244, 114, 182, 0.6)',
  },
  default: {
    base: '#9ca3af', // Gray
    glow: 'rgba(156, 163, 175, 0.3)',
    border: 'rgba(156, 163, 175, 0.6)',
  },
};

/**
 * Get color scheme for a node based on its type
 */
export function getNodeColor(node) {
  if (!node?.id) return NODE_COLORS.default;

  // Node IDs use hyphen format: "note-123", "tag-456", "image-789"
  const [type] = node.id.split('-');
  return NODE_COLORS[type] || NODE_COLORS.default;
}

/**
 * Calculate node size based on connections
 * Smaller defaults to prevent overlapping when zoomed in
 */
export function getNodeSize(node, { minSize = 2, maxSize = 8, baseSize = 3 } = {}) {
  const connections = node.connections || node.val || 1;
  // Scale more gently: sqrt provides diminishing returns for hub nodes
  const size = baseSize + Math.sqrt(connections) * 0.8;
  return Math.min(Math.max(size, minSize), maxSize);
}

/**
 * Render a node on canvas context
 */
export function renderNode(ctx, node, globalScale, state = {}) {
  const { isSelected, isHovered, isFocused, isPinned } = state;
  const colors = getNodeColor(node);
  const size = getNodeSize(node);

  // Save context state
  ctx.save();

  // Draw glow for selected/hovered nodes
  if (isSelected || isHovered) {
    ctx.beginPath();
    ctx.arc(node.x, node.y, size + 8, 0, 2 * Math.PI);
    ctx.fillStyle = colors.glow;
    ctx.fill();
  }

  // Draw focus ring for focused node
  if (isFocused) {
    ctx.beginPath();
    ctx.arc(node.x, node.y, size + 4, 0, 2 * Math.PI);
    ctx.strokeStyle = colors.base;
    ctx.lineWidth = 2;
    ctx.stroke();
  }

  // Draw node circle
  ctx.beginPath();
  ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
  ctx.fillStyle = isSelected ? colors.base : colors.border;
  ctx.fill();

  // Draw border
  ctx.strokeStyle = colors.base;
  ctx.lineWidth = isSelected ? 2 : 1;
  ctx.stroke();

  // Draw pin indicator - theme aware
  if (isPinned) {
    ctx.beginPath();
    ctx.arc(node.x, node.y - size - 4, 3, 0, 2 * Math.PI);
    ctx.fillStyle = isLightTheme() ? '#374151' : '#f9fafb';
    ctx.fill();
  }

  // Restore context state
  ctx.restore();
}

/**
 * Render node label
 */
export function renderNodeLabel(ctx, node, globalScale, state = {}) {
  const { isSelected, isHovered, showAllLabels = false } = state;
  const shouldShow = isSelected || isHovered || showAllLabels || (node.isHub && globalScale > 1);

  if (!shouldShow) return;

  const size = getNodeSize(node);
  const fontSize = Math.max(10, 12 / globalScale);
  const label = truncateLabel(node.title || node.id, 20);

  ctx.save();

  // Theme-aware colors for legibility
  const lightMode = isLightTheme();
  const bgColor = lightMode ? 'rgba(255, 255, 255, 0.9)' : 'rgba(0, 0, 0, 0.8)';
  const textColor = lightMode ? '#1f2937' : '#f9fafb';

  // Background for legibility
  ctx.font = `${fontSize}px Inter, sans-serif`;
  const textWidth = ctx.measureText(label).width;
  const padding = 4;

  ctx.fillStyle = bgColor;
  ctx.fillRect(
    node.x - textWidth / 2 - padding,
    node.y + size + 4,
    textWidth + padding * 2,
    fontSize + padding
  );

  // Text
  ctx.fillStyle = textColor;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  ctx.fillText(label, node.x, node.y + size + 6);

  ctx.restore();
}

/**
 * Truncate label to max length
 */
function truncateLabel(text, maxLength) {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 1) + '\u2026';
}

/**
 * Get node icon based on type (for future SVG icons)
 */
export function getNodeIcon(node) {
  if (!node?.id) return 'circle';

  // Node IDs use hyphen format: "note-123", "tag-456", "image-789"
  const [type] = node.id.split('-');
  const icons = {
    note: 'file-text',
    tag: 'tag',
    image: 'image',
    media: 'image',
    entity: 'sparkles',
    collection: 'folder',
  };

  return icons[type] || 'circle';
}
