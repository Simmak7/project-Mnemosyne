// Gallery Feature - Public API
// 3-column photo gallery with Neural Glass design

// Main layout component
export { default as GalleryLayout } from './components/GalleryLayout';

// Sub-components (for advanced usage)
export { default as GallerySidebar } from './components/GallerySidebar';
export { default as GalleryGrid } from './components/GalleryGrid';
export { default as GalleryContextPanel } from './components/GalleryContextPanel';
export { default as TimelineScrubber } from './components/TimelineScrubber';
export { default as PhotoThumbnail } from './components/PhotoThumbnail';
export { default as ImageLightbox } from './components/ImageLightbox';
export { default as BlurHashPlaceholder } from './components/BlurHashPlaceholder';
export { default as AlbumPicker } from './components/AlbumPicker';

// Hooks
export { useGalleryImages, useGalleryTags } from './hooks/useGalleryImages';
export { useAlbums, useAlbumImages } from './hooks/useAlbums';

// Utilities
export {
  calculateJustifiedLayout,
  groupImagesByDate,
  extractTimelineMarkers,
  estimateRowCount,
  preloadImageDimensions
} from './utils/justifiedLayout';
