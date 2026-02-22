import { useState, useCallback } from 'react';
import { transformToGraphData } from '../../../../utils/graphDataTransform';
import { API_URL } from '../../../../utils/api';

/**
 * Hook for fetching and managing graph data
 */
export function useGraphData() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchGraphData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem('token');

      if (!token) {
        throw new Error('No authentication token found');
      }

      // Fetch all notes with their relationships
      const notesResponse = await fetch(`${API_URL}/notes-enhanced/`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (!notesResponse.ok) {
        if (notesResponse.status === 401 || notesResponse.status === 403) {
          localStorage.removeItem('token');
          localStorage.removeItem('username');
          window.location.reload();
          return;
        }
        throw new Error('Failed to fetch notes');
      }

      const notes = await notesResponse.json();

      // Fetch all tags
      const tagsResponse = await fetch(`${API_URL}/tags/`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      const tags = tagsResponse.ok ? await tagsResponse.json() : [];

      // Fetch all images
      const imagesResponse = await fetch(`${API_URL}/images/`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      const images = imagesResponse.ok ? await imagesResponse.json() : [];

      // Transform data into graph format
      const graphData = transformToGraphData(notes, tags, images);
      setGraphData(graphData);
    } catch (err) {
      console.error('Error fetching graph data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    graphData,
    loading,
    error,
    fetchGraphData,
  };
}
