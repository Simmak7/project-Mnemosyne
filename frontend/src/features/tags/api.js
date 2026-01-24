/**
 * Tags Feature - API Functions
 *
 * API utilities for tag management operations.
 */

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Get auth headers for API requests.
 * @returns {Object} Headers object with Authorization
 */
const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };
};

/**
 * Tags API utilities
 */
export const tagsApi = {
  /**
   * Fetch all tags for the current user.
   * @returns {Promise<Array>} Array of tag objects
   */
  async fetchTags() {
    const response = await fetch(`${API_BASE}/tags/`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch tags');
    }

    return response.json();
  },

  /**
   * Create a new tag (or get existing if already exists).
   * @param {string} name - Tag name
   * @returns {Promise<Object>} Created/existing tag object
   */
  async createTag(name) {
    const response = await fetch(`${API_BASE}/tags/`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ name }),
    });

    if (!response.ok) {
      throw new Error('Failed to create tag');
    }

    return response.json();
  },

  /**
   * Add a tag to an image.
   * @param {number} imageId - Image ID
   * @param {string} tagName - Tag name
   * @returns {Promise<Object>} Response with tag_id and tag_name
   */
  async addTagToImage(imageId, tagName) {
    const response = await fetch(`${API_BASE}/images/${imageId}/tags/${tagName}`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to add tag to image');
    }

    return response.json();
  },

  /**
   * Remove a tag from an image.
   * @param {number} imageId - Image ID
   * @param {number} tagId - Tag ID
   * @returns {Promise<Object>} Response with status
   */
  async removeTagFromImage(imageId, tagId) {
    const response = await fetch(`${API_BASE}/images/${imageId}/tags/${tagId}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to remove tag from image');
    }

    return response.json();
  },

  /**
   * Add a tag to a note.
   * @param {number} noteId - Note ID
   * @param {string} tagName - Tag name
   * @returns {Promise<Object>} Response with tag_id and tag_name
   */
  async addTagToNote(noteId, tagName) {
    const response = await fetch(`${API_BASE}/notes/${noteId}/tags/${tagName}`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to add tag to note');
    }

    return response.json();
  },

  /**
   * Remove a tag from a note.
   * @param {number} noteId - Note ID
   * @param {number} tagId - Tag ID
   * @returns {Promise<Object>} Response with status
   */
  async removeTagFromNote(noteId, tagId) {
    const response = await fetch(`${API_BASE}/notes/${noteId}/tags/${tagId}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to remove tag from note');
    }

    return response.json();
  },
};

export default tagsApi;
