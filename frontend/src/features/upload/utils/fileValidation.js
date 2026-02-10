/**
 * File Validation Utilities
 * Extracted from ImageUpload.js for reuse
 */

// Maximum file size in bytes (10MB for images, 50MB for PDFs)
export const MAX_FILE_SIZE = 10 * 1024 * 1024;
export const MAX_PDF_SIZE = 50 * 1024 * 1024;

// Allowed MIME types
export const ALLOWED_TYPES = {
  // Images
  'image/jpeg': { ext: '.jpg', label: 'JPEG Image', icon: 'image' },
  'image/png': { ext: '.png', label: 'PNG Image', icon: 'image' },
  'image/gif': { ext: '.gif', label: 'GIF Image', icon: 'image' },
  'image/webp': { ext: '.webp', label: 'WebP Image', icon: 'image' },

  // Documents
  'application/pdf': { ext: '.pdf', label: 'PDF Document', icon: 'document' },
};

/**
 * Validate a single file
 * @param {File} file - File to validate
 * @returns {{ valid: boolean, error?: string, fileType?: object }}
 */
export function validateFile(file) {
  if (!file) {
    return { valid: false, error: 'No file provided' };
  }

  // Check file type
  const fileType = ALLOWED_TYPES[file.type];
  if (!fileType) {
    const allowedList = Object.values(ALLOWED_TYPES)
      .map(t => t.label)
      .join(', ');
    return {
      valid: false,
      error: `Unsupported file type. Allowed: ${allowedList}`
    };
  }

  // Check file size (PDFs get higher limit)
  const maxSize = file.type === 'application/pdf' ? MAX_PDF_SIZE : MAX_FILE_SIZE;
  if (file.size > maxSize) {
    const sizeMB = (maxSize / (1024 * 1024)).toFixed(0);
    return {
      valid: false,
      error: `File size exceeds ${sizeMB}MB limit`
    };
  }

  // Check for empty file
  if (file.size === 0) {
    return { valid: false, error: 'File is empty' };
  }

  return { valid: true, fileType };
}

/**
 * Validate multiple files
 * @param {FileList|File[]} files - Files to validate
 * @returns {{ valid: File[], invalid: Array<{ file: File, error: string }> }}
 */
export function validateFiles(files) {
  const valid = [];
  const invalid = [];

  Array.from(files).forEach(file => {
    const result = validateFile(file);
    if (result.valid) {
      valid.push(file);
    } else {
      invalid.push({ file, error: result.error });
    }
  });

  return { valid, invalid };
}

/**
 * Get human-readable file size
 * @param {number} bytes - File size in bytes
 * @returns {string} - Formatted size string
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';

  const units = ['B', 'KB', 'MB', 'GB'];
  const k = 1024;
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${units[i]}`;
}

/**
 * Get file type info from MIME type
 * @param {string} mimeType - MIME type string
 * @returns {object|null} - File type info or null
 */
export function getFileTypeInfo(mimeType) {
  return ALLOWED_TYPES[mimeType] || null;
}

/**
 * Check if file is an image
 * @param {File} file - File to check
 * @returns {boolean}
 */
export function isImageFile(file) {
  return file.type.startsWith('image/');
}

/**
 * Get accept string for file input
 * @returns {string} - Accept attribute value
 */
export function getAcceptString() {
  return Object.keys(ALLOWED_TYPES).join(',');
}
