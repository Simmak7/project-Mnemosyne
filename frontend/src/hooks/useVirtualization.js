import { useVirtualizer } from '@tanstack/react-virtual';
import { useRef, useMemo } from 'react';

/**
 * Custom hook for virtualization with TanStack Virtual
 * @param {Object} options - Virtualization options
 * @param {Array} options.items - Array of items to virtualize
 * @param {Function} options.estimateSize - Function to estimate item size
 * @param {number} options.overscan - Number of items to render outside viewport
 * @returns {Object} - Virtualizer instance and helper methods
 */
function useVirtualization({ items = [], estimateSize, overscan = 5 }) {
  const parentRef = useRef(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: estimateSize || (() => 100), // Default 100px per item
    overscan,
    // Enable smooth scrolling
    scrollMargin: parentRef.current?.offsetTop || 0,
  });

  const virtualItems = virtualizer.getVirtualItems();

  // Calculate total size
  const totalSize = virtualizer.getTotalSize();

  // Helper to scroll to specific index
  const scrollToIndex = (index, options = {}) => {
    virtualizer.scrollToIndex(index, {
      align: 'start',
      ...options,
    });
  };

  // Helper to scroll to top
  const scrollToTop = () => {
    virtualizer.scrollToOffset(0);
  };

  return {
    parentRef,
    virtualizer,
    virtualItems,
    totalSize,
    scrollToIndex,
    scrollToTop,
  };
}

export default useVirtualization;
