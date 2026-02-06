import React from 'react';
import { Calendar } from 'lucide-react';
import PhotoThumbnail from '../../PhotoThumbnail';

/**
 * Virtualized row renderer for gallery grid
 * Memoized to prevent re-renders when parent scrolls
 */
function VirtualizedRow({
  row,
  virtualItem,
  measureElement,
  showFilenames,
  showTags,
  isTrashView,
  onOpenLightbox,
  onToggleFavorite,
  onMoveToTrash,
  onRetryAnalysis,
  onRestoreFromTrash,
  onPermanentDelete,
}) {
  if (!row) return null;

  return (
    <div
      key={virtualItem.key}
      data-index={virtualItem.index}
      ref={measureElement}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        transform: `translateY(${virtualItem.start}px)`,
      }}
    >
      {row.type === 'date-header' ? (
        <div className="date-header">
          <Calendar size={16} />
          <span>{row.label}</span>
        </div>
      ) : (
        <div
          className="image-row"
          style={{
            display: 'flex',
            gap: '4px',
            height: row.height,
          }}
        >
          {row.images.map((image) => (
            <PhotoThumbnail
              key={image.id}
              image={image}
              width={image.finalWidth}
              height={image.finalHeight}
              showFilename={showFilenames}
              showTags={showTags}
              onImageClick={onOpenLightbox}
              onFavorite={onToggleFavorite}
              onDelete={onMoveToTrash}
              onRetry={onRetryAnalysis}
              onRestore={onRestoreFromTrash}
              onPermanentDelete={onPermanentDelete}
              isTrashView={isTrashView}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default React.memo(VirtualizedRow);
