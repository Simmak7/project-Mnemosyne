/**
 * useGalleryData - Data fetching and management for image gallery
 */
import { useState, useCallback } from 'react';

export function useGalleryData() {
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [allTags, setAllTags] = useState([]);
  const [retryingImages, setRetryingImages] = useState(new Set());
  const [deletingImages, setDeletingImages] = useState(new Set());
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');

  const showMessage = useCallback((text, type) => {
    setMessage(text);
    setMessageType(type);
    setTimeout(() => setMessage(''), type === 'error' ? 5000 : 3000);
  }, []);

  const fetchImages = useCallback(async (pageNum) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        console.error('No token found');
        return [];
      }

      const response = await fetch(
        `http://localhost:8000/images/?skip=${(pageNum - 1) * 50}&limit=50`,
        {
          headers: { 'Authorization': `Bearer ${token}` },
        }
      );

      if (response.ok) {
        return await response.json();
      } else if (response.status === 401 || response.status === 403) {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        window.location.reload();
      }
      return [];
    } catch (error) {
      console.error('Error fetching images:', error);
      return [];
    }
  }, []);

  const fetchTags = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await fetch('http://localhost:8000/tags/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setAllTags(data);
      }
    } catch (error) {
      console.error('Error fetching tags:', error);
    }
  }, []);

  const retryImageAnalysis = useCallback(async (imageId) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        showMessage('Please login to retry image analysis', 'error');
        return;
      }

      setRetryingImages(prev => new Set([...prev, imageId]));
      setImages(prevImages =>
        prevImages.map(img =>
          img.id === imageId ? { ...img, ai_analysis_status: 'processing' } : img
        )
      );

      const response = await fetch(`http://localhost:8000/retry-image/${imageId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        showMessage('AI analysis re-queued successfully! Processing...', 'success');
        setTimeout(() => {
          setRetryingImages(prev => {
            const newSet = new Set(prev);
            newSet.delete(imageId);
            return newSet;
          });
        }, 2000);
      } else if (response.status === 401 || response.status === 403) {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        window.location.reload();
      } else {
        const errorData = await response.json();
        showMessage(`Failed to retry: ${errorData.detail || 'Unknown error'}`, 'error');
        setImages(prevImages =>
          prevImages.map(img =>
            img.id === imageId ? { ...img, ai_analysis_status: 'failed' } : img
          )
        );
        setRetryingImages(prev => {
          const newSet = new Set(prev);
          newSet.delete(imageId);
          return newSet;
        });
      }
    } catch (error) {
      console.error('Error retrying image analysis:', error);
      showMessage(`Network error: ${error.message}`, 'error');
      setImages(prevImages =>
        prevImages.map(img =>
          img.id === imageId ? { ...img, ai_analysis_status: 'failed' } : img
        )
      );
      setRetryingImages(prev => {
        const newSet = new Set(prev);
        newSet.delete(imageId);
        return newSet;
      });
    }
  }, [showMessage]);

  const handleDeleteImage = useCallback(async (imageId, onSuccess) => {
    const token = localStorage.getItem('token');
    if (!token) {
      console.error('No token found');
      return;
    }

    setDeletingImages(prev => new Set(prev).add(imageId));

    try {
      const response = await fetch(`http://localhost:8000/images/${imageId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        setImages(prevImages => prevImages.filter(img => img.id !== imageId));
        if (onSuccess) onSuccess();
      } else if (response.status === 401 || response.status === 403) {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        window.location.reload();
      } else {
        const errorData = await response.json();
        alert('Failed to delete image: ' + (errorData.detail || 'Unknown error'));
      }
    } catch (error) {
      console.error('Delete failed:', error);
      alert('Failed to delete image. Please try again.');
    } finally {
      setDeletingImages(prev => {
        const newSet = new Set(prev);
        newSet.delete(imageId);
        return newSet;
      });
    }
  }, []);

  const loadMore = useCallback(async () => {
    if (loading || !hasMore) return;

    setLoading(true);
    const nextPage = page + 1;
    const newImages = await fetchImages(nextPage);

    if (newImages.length === 0) {
      setHasMore(false);
    } else {
      setImages(prev => [...prev, ...newImages]);
      setPage(nextPage);
      setHasMore(newImages.length === 50);
    }
    setLoading(false);
  }, [fetchImages, page, loading, hasMore]);

  return {
    images, setImages,
    loading, setLoading,
    page, setPage,
    hasMore, setHasMore,
    allTags,
    retryingImages,
    deletingImages,
    message, messageType,
    fetchImages, fetchTags,
    retryImageAnalysis, handleDeleteImage,
    loadMore,
  };
}

export default useGalleryData;
