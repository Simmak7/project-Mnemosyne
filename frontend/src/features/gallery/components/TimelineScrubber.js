import React, { useState, useCallback, useRef, useEffect } from 'react';
import './TimelineScrubber.css';

/**
 * TimelineScrubber - Date navigation scrubber on right edge
 * Shows months/years, click to jump, drag to scrub
 */
function TimelineScrubber({ markers, activeMarker, onMarkerClick }) {
  const [isDragging, setIsDragging] = useState(false);
  const [hoverMarker, setHoverMarker] = useState(null);
  const [indicatorTop, setIndicatorTop] = useState(0);
  const scrubberRef = useRef(null);
  const markerRefs = useRef({});

  // Function to update indicator position
  const updateIndicatorPosition = useCallback(() => {
    if (activeMarker && markerRefs.current[activeMarker] && scrubberRef.current) {
      const markerEl = markerRefs.current[activeMarker];
      const scrubber = scrubberRef.current;
      const scrubberRect = scrubber.getBoundingClientRect();
      const markerRect = markerEl.getBoundingClientRect();

      // Calculate position relative to scrubber viewport (not scroll position)
      const relativeTop = markerRect.top - scrubberRect.top + (markerRect.height / 2);
      setIndicatorTop(relativeTop);
    }
  }, [activeMarker]);

  // Update indicator position and scroll to active marker when active marker changes
  useEffect(() => {
    if (activeMarker && markerRefs.current[activeMarker] && scrubberRef.current) {
      const markerEl = markerRefs.current[activeMarker];
      const scrubber = scrubberRef.current;

      // Auto-scroll scrubber to keep active marker in view
      const markerTopInScrubber = markerEl.offsetTop;
      const markerBottom = markerTopInScrubber + markerEl.offsetHeight;
      const visibleTop = scrubber.scrollTop;
      const visibleBottom = visibleTop + scrubber.clientHeight;

      // If marker is above visible area, scroll up
      if (markerTopInScrubber < visibleTop + 50) {
        scrubber.scrollTo({
          top: Math.max(0, markerTopInScrubber - 50),
          behavior: 'smooth'
        });
      }
      // If marker is below visible area, scroll down
      else if (markerBottom > visibleBottom - 50) {
        scrubber.scrollTo({
          top: markerBottom - scrubber.clientHeight + 50,
          behavior: 'smooth'
        });
      }

      // Update indicator position
      updateIndicatorPosition();
    }
  }, [activeMarker, updateIndicatorPosition]);

  // Update indicator position when scrubber scrolls
  useEffect(() => {
    const scrubber = scrubberRef.current;
    if (!scrubber) return;

    const handleScrubberScroll = () => {
      updateIndicatorPosition();
    };

    scrubber.addEventListener('scroll', handleScrubberScroll);
    return () => scrubber.removeEventListener('scroll', handleScrubberScroll);
  }, [updateIndicatorPosition]);

  // Handle mouse down for drag scrubbing
  const handleMouseDown = useCallback((e) => {
    setIsDragging(true);
    handleDrag(e);
  }, []);

  // Handle drag movement
  const handleDrag = useCallback((e) => {
    if (!scrubberRef.current || !markers.length) return;

    const rect = scrubberRef.current.getBoundingClientRect();
    const y = e.clientY - rect.top;
    const percentage = Math.max(0, Math.min(1, y / rect.height));
    const index = Math.floor(percentage * markers.length);
    const marker = markers[Math.min(index, markers.length - 1)];

    if (marker) {
      onMarkerClick(marker);
    }
  }, [markers, onMarkerClick]);

  // Handle mouse move during drag
  const handleMouseMove = useCallback((e) => {
    if (isDragging) {
      handleDrag(e);
    }
  }, [isDragging, handleDrag]);

  // Handle mouse up to end drag
  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  // Add global listeners for drag
  React.useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  if (!markers || markers.length === 0) {
    return null;
  }

  // Group markers by year for display
  const markersByYear = markers.reduce((acc, marker) => {
    if (!acc[marker.year]) {
      acc[marker.year] = [];
    }
    acc[marker.year].push(marker);
    return acc;
  }, {});

  return (
    <div
      ref={scrubberRef}
      className={`timeline-scrubber ${isDragging ? 'dragging' : ''}`}
      onMouseDown={handleMouseDown}
    >
      <div className="scrubber-track">
        {Object.entries(markersByYear).sort(([a], [b]) => Number(b) - Number(a)).map(([year, yearMarkers]) => (
          <div key={year} className="year-group">
            <div className="year-label">{year}</div>
            <div className="month-markers">
              {yearMarkers.map((marker) => {
                const isActive = activeMarker === marker.key;
                const isHovered = hoverMarker === marker.key;

                return (
                  <button
                    key={marker.key}
                    ref={(el) => { markerRefs.current[marker.key] = el; }}
                    className={`month-marker ${isActive ? 'active' : ''} ${isHovered ? 'hovered' : ''}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      onMarkerClick(marker);
                    }}
                    onMouseEnter={() => setHoverMarker(marker.key)}
                    onMouseLeave={() => setHoverMarker(null)}
                    title={`${marker.month} ${marker.year} (${marker.count} photos)`}
                  >
                    <span className="month-label">{marker.month}</span>
                    {(isActive || isHovered) && (
                      <span className="marker-count">{marker.count}</span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Active indicator line */}
      {activeMarker && (
        <div
          className="scrubber-indicator active"
          style={{ top: indicatorTop }}
        />
      )}
    </div>
  );
}

export default TimelineScrubber;
