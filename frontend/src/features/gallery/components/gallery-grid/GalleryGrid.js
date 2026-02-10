import React, { useRef, useMemo } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import TimelineScrubber from '../TimelineScrubber';
import ImageLightbox from '../ImageLightbox';
import { useGalleryGridState, useContainerWidth, useScrollTimeline, useLightbox } from './hooks';
import { EmptyState, GridHeader, LoadingState, VirtualizedRow } from './components';
import { calculateLayoutRows, getDateGroups, getTimelineMarkers } from './utils';
import '../GalleryGrid.css';

/**
 * GalleryGrid - Center panel with justified photo grid
 * Features: Justified layout, date grouping, virtual scrolling, timeline scrubber
 */
function GalleryGrid({
  currentView,
  selectedAlbumId,
  selectedTags,
  sortBy,
  sortOrder,
  rowHeight,
  showFilenames,
  showDateHeaders,
  showTags,
  onNavigateToNote,
  onNavigateToAI,
  isSearchMode = false,
  searchResults = [],
  selectedImageId = null,
  onClearImageSelection,
}) {
  const containerRef = useRef(null);
  const containerWidth = useContainerWidth(containerRef);

  // Gallery state hook
  const {
    images,
    sortedImages,
    isLoading,
    dimensionsLoaded,
    isTrashView,
    isAlbumView,
    currentAlbum,
    toggleFavorite,
    moveToTrash,
    restoreFromTrash,
    permanentDelete,
    retryAnalysis,
    renameImage,
  } = useGalleryGridState({
    currentView,
    selectedAlbumId,
    selectedTags,
    sortBy,
    sortOrder,
    isSearchMode,
    searchResults,
  });

  // Lightbox hook
  const {
    selectedImage,
    openLightbox,
    closeLightbox,
    handleLightboxNavigate,
    handleRenameImage,
  } = useLightbox({
    sortedImages,
    images,
    selectedImageId,
    onClearImageSelection,
    renameImage,
  });

  // Calculate layout
  const dateGroups = useMemo(
    () => getDateGroups(sortedImages, showDateHeaders),
    [sortedImages, showDateHeaders]
  );

  const timelineMarkers = useMemo(
    () => getTimelineMarkers(sortedImages),
    [sortedImages]
  );

  const layoutRows = useMemo(
    () => calculateLayoutRows(dateGroups, containerWidth, rowHeight, showDateHeaders),
    [dateGroups, containerWidth, rowHeight, showDateHeaders]
  );

  // Virtual scrolling
  const virtualizer = useVirtualizer({
    count: layoutRows.length,
    getScrollElement: () => containerRef.current,
    estimateSize: (index) => {
      const row = layoutRows[index];
      if (row?.type === 'date-header') return 48;
      return row?.height || rowHeight;
    },
    overscan: 3,
  });

  // Scroll timeline hook
  const { activeTimelineMarker, handleScroll, handleTimelineClick } = useScrollTimeline(
    containerRef,
    layoutRows,
    virtualizer
  );

  // Empty state
  if (!isLoading && sortedImages.length === 0) {
    return (
      <EmptyState
        isSearchMode={isSearchMode}
        isAlbumView={isAlbumView}
        currentAlbum={currentAlbum}
        currentView={currentView}
      />
    );
  }

  return (
    <div className="gallery-grid-container">
      <GridHeader
        isSearchMode={isSearchMode}
        isAlbumView={isAlbumView}
        currentAlbum={currentAlbum}
        currentView={currentView}
        imageCount={sortedImages.length}
        hasFilter={selectedTags.length > 0}
      />

      <LoadingState isLoading={isLoading} dimensionsLoaded={dimensionsLoaded} />

      <div className="gallery-grid-area">
        <TimelineScrubber
          markers={timelineMarkers}
          activeMarker={activeTimelineMarker}
          onMarkerClick={handleTimelineClick}
        />

        <div
          ref={containerRef}
          className="gallery-scroll-container"
          onScroll={handleScroll}
        >
          <div
            style={{
              height: `${virtualizer.getTotalSize()}px`,
              width: '100%',
              position: 'relative',
            }}
          >
            {virtualizer.getVirtualItems().map((virtualItem) => (
              <VirtualizedRow
                key={virtualItem.key}
                row={layoutRows[virtualItem.index]}
                virtualItem={virtualItem}
                measureElement={virtualizer.measureElement}
                showFilenames={showFilenames}
                showTags={showTags}
                isTrashView={isTrashView}
                onOpenLightbox={openLightbox}
                onToggleFavorite={toggleFavorite}
                onMoveToTrash={moveToTrash}
                onRetryAnalysis={retryAnalysis}
                onRestoreFromTrash={restoreFromTrash}
                onPermanentDelete={permanentDelete}
              />
            ))}
          </div>
        </div>
      </div>

      {selectedImage && (
        <ImageLightbox
          image={selectedImage}
          onClose={closeLightbox}
          onNavigate={handleLightboxNavigate}
          onNavigateToNote={onNavigateToNote}
          onNavigateToAI={onNavigateToAI}
          onFavorite={() => toggleFavorite(selectedImage.id)}
          onRetry={() => retryAnalysis(selectedImage.id)}
          onDelete={() => {
            moveToTrash(selectedImage.id);
            closeLightbox();
          }}
          onRename={handleRenameImage}
        />
      )}
    </div>
  );
}

export default GalleryGrid;
