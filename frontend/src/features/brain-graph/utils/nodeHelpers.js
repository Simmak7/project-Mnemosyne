/**
 * nodeHelpers.js - Shared node ID/path utilities
 */

import { formatDistanceToNow } from 'date-fns';

/** Format a date string as relative time (e.g., "2 hours ago") */
export function formatDate(dateStr) {
  try {
    return formatDistanceToNow(new Date(dateStr), { addSuffix: true });
  } catch {
    return dateStr;
  }
}

/** Extract numeric ID from node ID (e.g., "image-123" -> "123") */
export function getNodeId(node) {
  if (!node?.id) return '';
  const [, ...idParts] = node.id.split('-');
  return idParts.join('-');
}

/** Get navigation path for a node (e.g., "note-123" -> "/notes/123") */
export function getNodePath(node) {
  const [type, ...idParts] = node.id.split('-');
  const id = idParts.join('-');
  switch (type) {
    case 'note': return `/notes/${id}`;
    case 'image': return `/gallery?image=${id}`;
    case 'tag': return `/tags/${encodeURIComponent(id)}`;
    case 'document': return `/documents/${id}`;
    default: return '/';
  }
}
