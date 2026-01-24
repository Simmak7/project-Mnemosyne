/**
 * Brain Graph Feature - Public Exports
 *
 * Neural Glass-styled knowledge graph visualization.
 * Navigation-first design with insight mode for discovery.
 */

// Main component
export { BrainGraph } from './components/BrainGraph';
export { BrainGraphPreview } from './components/BrainGraphPreview';

// Individual views for direct use
export { ExploreView } from './views/ExploreView';
export { MapView } from './views/MapView';
export { MediaView } from './views/MediaView';
export { PathFinderView } from './views/PathFinderView';

// Hooks
export { useGraphData } from './hooks/useGraphData';
export { useGraphState } from './hooks/useGraphState';
export { useGraphLayout } from './hooks/useGraphLayout';
export { useGraphFilters } from './hooks/useGraphFilters';

// Utils (internal, but exposed for extension)
export { getNodeColor, renderNode } from './utils/nodeRendering';
export { getEdgeColor, renderEdge } from './utils/edgeRendering';
export { LAYOUT_PRESETS, getLayoutConfig } from './utils/layoutPresets';
