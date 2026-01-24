import React, { useState, useEffect, useRef } from 'react';
import { useInView } from 'react-intersection-observer';
import './LazyImage.css';

// Simple in-memory cache for blob URLs to persist across navigation
const imageCache = new Map();

/**
 * Lazy-loaded image component with intersection observer
 * Loads image only when it enters viewport
 */
function LazyImage({ src, alt, className, style, onClick, imageId }) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState(false);
  const [imageSrc, setImageSrc] = useState(null);
  const isMounted = useRef(true);
  const { ref, inView } = useInView({
    triggerOnce: false, // Allow re-triggering when coming back into view
    threshold: 0.1,
  });

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  useEffect(() => {
    if (inView && src && !imageSrc && !error) {
      // Check cache first
      const cacheKey = imageId || src;
      if (imageCache.has(cacheKey)) {
        setImageSrc(imageCache.get(cacheKey));
        return;
      }

      // Fetch image when in view
      const loadImage = async () => {
        try {
          const token = localStorage.getItem('token');
          const response = await fetch(src, {
            headers: token ? { 'Authorization': `Bearer ${token}` } : {},
          });

          if (response.ok) {
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);

            // Cache the URL
            imageCache.set(cacheKey, url);

            if (isMounted.current) {
              setImageSrc(url);
            }
          } else {
            if (isMounted.current) {
              setError(true);
            }
          }
        } catch (err) {
          console.error('Error loading image:', err);
          if (isMounted.current) {
            setError(true);
          }
        }
      };

      loadImage();
    }
  }, [inView, src, imageSrc, error, imageId]);

  // Reset error state if src changes
  useEffect(() => {
    setError(false);
    setIsLoaded(false);

    // Check if we have a cached version
    const cacheKey = imageId || src;
    if (imageCache.has(cacheKey)) {
      setImageSrc(imageCache.get(cacheKey));
    } else {
      setImageSrc(null);
    }
  }, [src, imageId]);

  const handleLoad = () => {
    setIsLoaded(true);
  };

  const handleError = () => {
    setError(true);
  };

  return (
    <div
      ref={ref}
      className={`lazy-image-container ${className || ''}`}
      style={style}
      onClick={onClick}
    >
      {!isLoaded && !error && (
        <div className="lazy-image-placeholder">
          <div className="lazy-image-skeleton"></div>
        </div>
      )}

      {error && (
        <div className="lazy-image-error">
          <span>❌</span>
          <p>Failed to load</p>
        </div>
      )}

      {imageSrc && !error && (
        <img
          src={imageSrc}
          alt={alt}
          className={`lazy-image ${isLoaded ? 'loaded' : ''}`}
          onLoad={handleLoad}
          onError={handleError}
        />
      )}
    </div>
  );
}

export default LazyImage;
