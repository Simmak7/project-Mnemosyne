/**
 * Note utility functions
 */
import { format } from 'date-fns';
import React from 'react';

/**
 * Format date for display
 */
export function formatDate(dateString) {
  try {
    return format(new Date(dateString), 'MMM dd, yyyy');
  } catch {
    return 'Unknown date';
  }
}

/**
 * Extract snippet from content
 */
export function getSnippet(content, maxLength = 150) {
  if (!content) return 'No content';
  // eslint-disable-next-line no-useless-escape
  const stripped = content.replace(/[#*`\[\]]/g, '').trim();
  return stripped.length > maxLength
    ? stripped.substring(0, maxLength) + '...'
    : stripped;
}

/**
 * Highlight search query in text
 */
export function highlightText(text, query) {
  if (!query || !text) return text;

  const parts = text.split(new RegExp(`(${query})`, 'gi'));
  return parts.map((part, index) =>
    part.toLowerCase() === query.toLowerCase() ? (
      <mark key={index} style={{ backgroundColor: '#ffd700', padding: '2px 4px', borderRadius: '3px' }}>
        {part}
      </mark>
    ) : (
      part
    )
  );
}
