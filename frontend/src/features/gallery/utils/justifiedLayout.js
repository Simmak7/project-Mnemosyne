/**
 * Justified Layout Algorithm (Enhanced)
 * Creates rows of images that fill container width while maintaining aspect ratios
 * Inspired by Flickr's justified-layout and Immich's implementation
 */

// Default aspect ratio for images without dimensions
const DEFAULT_ASPECT_RATIO = 1.5; // 3:2 landscape (common photo ratio)

// Aspect ratio limits to handle edge cases
const MIN_ASPECT_RATIO = 0.3;  // Very tall portrait (1:3.33)
const MAX_ASPECT_RATIO = 3.5;  // Very wide panorama (3.5:1)

/**
 * Calculate justified layout for images
 * Uses a linear partition algorithm for optimal row distribution
 *
 * @param {Array} images - Array of image objects with width/height
 * @param {number} containerWidth - Width of the container
 * @param {Object} options - Layout options
 * @returns {Array} Array of rows with positioned images
 */
export function calculateJustifiedLayout(images, containerWidth, options = {}) {
  const {
    targetRowHeight = 200,
    minRowHeight = 120,
    maxRowHeight = 350,
    lastRowBehavior = 'left', // 'left', 'justify', or 'center'
    boxSpacing = { horizontal: 4, vertical: 4 }
  } = options;

  if (!images || images.length === 0 || containerWidth <= 0) {
    return [];
  }

  // Normalize images with aspect ratios
  const normalizedImages = images.map((image, index) => {
    let aspectRatio = getAspectRatio(image);

    // Clamp extreme aspect ratios
    aspectRatio = Math.max(MIN_ASPECT_RATIO, Math.min(MAX_ASPECT_RATIO, aspectRatio));

    return {
      ...image,
      index,
      aspectRatio,
      originalAspectRatio: aspectRatio
    };
  });

  // Use greedy row-filling algorithm with look-ahead
  const rows = buildRows(normalizedImages, containerWidth, {
    targetRowHeight,
    minRowHeight,
    maxRowHeight,
    gap: boxSpacing.horizontal
  });

  // Finalize each row with exact dimensions
  return rows.map((rowImages, rowIndex) => {
    const isLastRow = rowIndex === rows.length - 1;
    return finalizeRow(
      rowImages,
      containerWidth,
      boxSpacing.horizontal,
      minRowHeight,
      maxRowHeight,
      targetRowHeight,
      isLastRow ? lastRowBehavior : 'justify'
    );
  });
}

/**
 * Get aspect ratio from image, with fallback detection
 */
function getAspectRatio(image) {
  // Use stored dimensions if available
  if (image.width && image.height && image.width > 0 && image.height > 0) {
    return image.width / image.height;
  }

  // Try to infer from filename (common patterns)
  if (image.filename) {
    const filename = image.filename.toLowerCase();
    // Portrait indicators
    if (filename.includes('portrait') || filename.includes('vertical')) {
      return 0.75; // 3:4 portrait
    }
    // Panorama indicators
    if (filename.includes('pano') || filename.includes('panorama') || filename.includes('wide')) {
      return 2.5; // Wide panorama
    }
  }

  // Default to common photo aspect ratio
  return DEFAULT_ASPECT_RATIO;
}

/**
 * Build rows using greedy algorithm with cost optimization
 * Tries to create rows that are close to target height
 */
function buildRows(images, containerWidth, options) {
  const { targetRowHeight, minRowHeight, maxRowHeight, gap } = options;
  const rows = [];
  let currentRow = [];
  let currentRowAspectSum = 0;

  for (let i = 0; i < images.length; i++) {
    const image = images[i];
    const newAspectSum = currentRowAspectSum + image.aspectRatio;

    // Calculate what height this row would be with current images + new image
    const gapsWidth = currentRow.length * gap;
    const availableWidth = containerWidth - gapsWidth - gap;
    const rowHeightWithNew = availableWidth / newAspectSum;

    // Calculate height without new image
    const rowHeightWithout = currentRow.length > 0
      ? (containerWidth - (currentRow.length - 1) * gap) / currentRowAspectSum
      : Infinity;

    // Decide whether to add to current row or start new row
    const shouldStartNewRow = currentRow.length > 0 && (
      // Row would be too short (images too wide)
      rowHeightWithNew < minRowHeight ||
      // Current row is closer to target than adding more
      (rowHeightWithout <= maxRowHeight &&
        Math.abs(rowHeightWithout - targetRowHeight) < Math.abs(rowHeightWithNew - targetRowHeight) &&
        rowHeightWithNew < targetRowHeight)
    );

    if (shouldStartNewRow) {
      rows.push(currentRow);
      currentRow = [image];
      currentRowAspectSum = image.aspectRatio;
    } else {
      currentRow.push(image);
      currentRowAspectSum = newAspectSum;
    }
  }

  // Don't forget the last row
  if (currentRow.length > 0) {
    rows.push(currentRow);
  }

  return rows;
}

/**
 * Finalize a row by calculating exact pixel dimensions
 */
function finalizeRow(rowImages, containerWidth, gap, minHeight, maxHeight, targetHeight, behavior) {
  if (rowImages.length === 0) {
    return { images: [], height: 0, width: 0 };
  }

  const numGaps = rowImages.length - 1;
  const totalGapWidth = numGaps * gap;
  const availableWidth = containerWidth - totalGapWidth;

  // Calculate total aspect ratio for the row
  const totalAspectRatio = rowImages.reduce((sum, img) => sum + img.aspectRatio, 0);

  // Calculate the height that makes images fit exactly
  let rowHeight = availableWidth / totalAspectRatio;

  // For last row with 'left' or 'center' behavior
  if (behavior === 'left' || behavior === 'center') {
    // Don't stretch beyond target height
    rowHeight = Math.min(rowHeight, targetHeight);

    // But ensure minimum height
    rowHeight = Math.max(rowHeight, minHeight);
  } else {
    // For justified rows, clamp to min/max
    rowHeight = Math.max(minHeight, Math.min(maxHeight, rowHeight));
  }

  // Calculate final dimensions for each image
  let xOffset = 0;

  // For center alignment on last row
  if (behavior === 'center') {
    const totalWidth = rowImages.reduce((sum, img) => sum + (rowHeight * img.aspectRatio), 0) + totalGapWidth;
    xOffset = Math.max(0, (containerWidth - totalWidth) / 2);
  }

  const images = rowImages.map((img) => {
    const width = rowHeight * img.aspectRatio;
    const result = {
      ...img,
      finalWidth: Math.round(width),
      finalHeight: Math.round(rowHeight),
      x: Math.round(xOffset),
      y: 0,
      // Include orientation info for styling
      orientation: getOrientation(img.aspectRatio)
    };
    xOffset += width + gap;
    return result;
  });

  // Calculate actual row width
  const actualWidth = images.reduce((sum, img) => sum + img.finalWidth, 0) + totalGapWidth;

  return {
    images,
    height: Math.round(rowHeight),
    width: Math.round(actualWidth),
    behavior
  };
}

/**
 * Determine image orientation from aspect ratio
 */
function getOrientation(aspectRatio) {
  if (aspectRatio < 0.9) return 'portrait';
  if (aspectRatio > 1.1) return 'landscape';
  return 'square';
}

/**
 * Group images by date for timeline display
 * @param {Array} images - Array of image objects with uploaded_at date
 * @param {Object} options - Grouping options
 * @returns {Array} Array of date groups
 */
export function groupImagesByDate(images, options = {}) {
  const { groupBy = 'day' } = options;

  if (!images || images.length === 0) {
    return [];
  }

  const groups = new Map();

  images.forEach(image => {
    const date = new Date(image.uploaded_at);
    let key;
    let label;

    if (groupBy === 'month') {
      key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      label = date.toLocaleDateString(undefined, { month: 'long', year: 'numeric' });
    } else if (groupBy === 'year') {
      key = `${date.getFullYear()}`;
      label = date.getFullYear().toString();
    } else {
      // Default: group by day
      key = date.toISOString().split('T')[0];
      label = formatDateLabel(date);
    }

    if (!groups.has(key)) {
      groups.set(key, {
        key,
        label,
        date: date.toISOString(),
        images: []
      });
    }
    groups.get(key).images.push(image);
  });

  // Sort groups by date (newest first)
  return Array.from(groups.values()).sort((a, b) =>
    new Date(b.date) - new Date(a.date)
  );
}

/**
 * Format date label with relative dates
 */
function formatDateLabel(date) {
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  if (date.toDateString() === today.toDateString()) {
    return 'Today';
  }

  if (date.toDateString() === yesterday.toDateString()) {
    return 'Yesterday';
  }

  // This week - show weekday
  const daysAgo = Math.floor((today - date) / (1000 * 60 * 60 * 24));
  if (daysAgo < 7) {
    return date.toLocaleDateString(undefined, {
      weekday: 'long',
      month: 'long',
      day: 'numeric'
    });
  }

  // Older - include year if different
  return date.toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: date.getFullYear() !== today.getFullYear() ? 'numeric' : undefined
  });
}

/**
 * Extract unique months/years from images for timeline scrubber
 */
export function extractTimelineMarkers(images) {
  if (!images || images.length === 0) {
    return [];
  }

  const markers = new Map();

  images.forEach(image => {
    const date = new Date(image.uploaded_at);
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;

    if (!markers.has(key)) {
      markers.set(key, {
        key,
        month: date.toLocaleDateString(undefined, { month: 'short' }),
        year: date.getFullYear(),
        date: new Date(date.getFullYear(), date.getMonth(), 1).toISOString(),
        count: 0
      });
    }
    markers.get(key).count++;
  });

  return Array.from(markers.values()).sort((a, b) =>
    new Date(b.date) - new Date(a.date)
  );
}

/**
 * Calculate optimal row count for a set of images
 * Useful for planning layout before rendering
 */
export function estimateRowCount(images, containerWidth, targetRowHeight = 200) {
  if (!images || images.length === 0 || containerWidth <= 0) {
    return 0;
  }

  const totalAspectRatio = images.reduce((sum, img) => {
    const ar = getAspectRatio(img);
    return sum + Math.max(MIN_ASPECT_RATIO, Math.min(MAX_ASPECT_RATIO, ar));
  }, 0);

  // Estimate total width if all images were at target height
  const totalWidth = totalAspectRatio * targetRowHeight;

  // Estimate number of rows needed
  return Math.ceil(totalWidth / containerWidth);
}

/**
 * Preload image dimensions for a batch of images
 * Returns a promise that resolves with images including width/height
 */
export async function preloadImageDimensions(images, getImageUrl) {
  const promises = images.map(async (image) => {
    if (image.width && image.height) {
      return image; // Already has dimensions
    }

    try {
      const dimensions = await loadImageDimensions(getImageUrl(image));
      return {
        ...image,
        width: dimensions.width,
        height: dimensions.height
      };
    } catch {
      // Return image with default aspect ratio if loading fails
      return {
        ...image,
        width: 300,
        height: 200
      };
    }
  });

  return Promise.all(promises);
}

/**
 * Load dimensions for a single image
 */
function loadImageDimensions(url) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      resolve({ width: img.naturalWidth, height: img.naturalHeight });
    };
    img.onerror = reject;
    img.src = url;
  });
}
