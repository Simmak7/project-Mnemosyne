/**
 * imageCache.js - Thumbnail cache for image graph nodes
 *
 * Loads image thumbnails on demand and caches them as HTMLImageElements.
 * LRU eviction at MAX_ENTRIES to bound memory usage.
 *
 * States per entry:
 *   undefined  = not started
 *   null       = loading in progress
 *   Image      = loaded and ready
 *   false      = load failed
 */

import { API_URL } from '../../../utils/api';

const MAX_ENTRIES = 100;

class ImageCache {
  constructor() {
    this._cache = new Map();
  }

  /**
   * Get cached image for a node. Returns:
   *   HTMLImageElement if loaded, null if loading, undefined if not started.
   * Triggers load on first access.
   */
  get(nodeId) {
    if (!nodeId) return undefined;

    const entry = this._cache.get(nodeId);
    if (entry !== undefined) return entry || undefined;

    // Start loading
    this._load(nodeId);
    return undefined;
  }

  _load(nodeId) {
    // Mark as loading
    this._cache.set(nodeId, null);
    this._evictIfNeeded();

    // Extract numeric ID from "image-123" format
    const numericId = nodeId.replace('image-', '');
    const url = `${API_URL}/images/${numericId}?thumbnail=true`;

    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      this._cache.set(nodeId, img);
    };
    img.onerror = () => {
      this._cache.set(nodeId, false);
    };
    img.src = url;
  }

  _evictIfNeeded() {
    if (this._cache.size <= MAX_ENTRIES) return;
    // Remove oldest entry (first key in Map insertion order)
    const first = this._cache.keys().next().value;
    this._cache.delete(first);
  }

  clear() {
    this._cache.clear();
  }
}

// Singleton instance
export const imageCache = new ImageCache();
