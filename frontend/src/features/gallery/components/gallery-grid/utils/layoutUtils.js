import {
  calculateJustifiedLayout,
  groupImagesByDate,
  extractTimelineMarkers,
} from '../../../utils/justifiedLayout';

/**
 * Calculate layout rows for gallery grid
 */
export function calculateLayoutRows(dateGroups, containerWidth, rowHeight, showDateHeaders) {
  if (containerWidth <= 0) return [];

  const rows = [];

  dateGroups.forEach(group => {
    // Add date header row
    if (showDateHeaders && group.label) {
      rows.push({
        type: 'date-header',
        key: `header-${group.key}`,
        label: group.label,
        date: group.date,
      });
    }

    // Calculate justified layout for this group's images
    const justifiedRows = calculateJustifiedLayout(group.images, containerWidth, {
      targetRowHeight: rowHeight,
      gap: 4,
    });

    // Add image rows
    justifiedRows.forEach((row, rowIndex) => {
      const rowDate = group.date || (row.images[0]?.uploaded_at);
      rows.push({
        type: 'image-row',
        key: `row-${group.key}-${rowIndex}`,
        images: row.images,
        height: row.height,
        width: row.width,
        date: rowDate,
      });
    });
  });

  return rows;
}

/**
 * Group sorted images by date
 */
export function getDateGroups(sortedImages, showDateHeaders) {
  if (!showDateHeaders) {
    return [{ key: 'all', label: '', images: sortedImages }];
  }
  return groupImagesByDate(sortedImages);
}

/**
 * Extract timeline markers from sorted images
 */
export function getTimelineMarkers(sortedImages) {
  return extractTimelineMarkers(sortedImages);
}
