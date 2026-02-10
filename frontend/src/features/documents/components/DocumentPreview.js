/**
 * DocumentPreview - Full-screen PDF viewer modal
 * Fetches PDF via authenticated API, creates blob URL for iframe display.
 * This avoids all CSP/cross-origin/cookie issues.
 */

import React, { useEffect, useCallback, useState, useRef } from 'react';
import { createPortal } from 'react-dom';
import { X, Download, FileText, Loader2 } from 'lucide-react';
import { API_URL } from '../../../utils/api';

import './DocumentPreview.css';

function DocumentPreview({ document: doc, onClose }) {
  const [blobUrl, setBlobUrl] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const blobUrlRef = useRef(null);

  const name = doc.display_name || doc.filename;
  const downloadUrl = `${API_URL}/documents/${doc.id}/file`;
  const size = doc.file_size
    ? `${(doc.file_size / (1024 * 1024)).toFixed(1)} MB`
    : '';

  // Fetch PDF as blob and create object URL
  useEffect(() => {
    let cancelled = false;

    async function fetchPdf() {
      try {
        const response = await fetch(
          `${API_URL}/documents/${doc.id}/file?inline=true`,
          { credentials: 'include' }
        );
        if (!response.ok) throw new Error(`Failed to load (${response.status})`);
        const blob = await response.blob();
        if (cancelled) return;
        const url = URL.createObjectURL(blob);
        blobUrlRef.current = url;
        setBlobUrl(url);
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchPdf();

    return () => {
      cancelled = true;
      if (blobUrlRef.current) URL.revokeObjectURL(blobUrlRef.current);
    };
  }, [doc.id]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'auto';
    };
  }, [onClose]);

  const handleBackdropClick = useCallback((e) => {
    if (e.target === e.currentTarget) onClose();
  }, [onClose]);

  return createPortal(
    <div className="doc-preview-overlay" onClick={handleBackdropClick}>
      <div className="doc-preview-content" onClick={(e) => e.stopPropagation()}>
        {/* Top bar */}
        <div className="doc-preview-topbar">
          <div className="doc-preview-title-area">
            <FileText size={16} className="doc-preview-title-icon" />
            <h2 className="doc-preview-title" title={name}>{name}</h2>
            {doc.page_count && (
              <span className="doc-preview-pages">{doc.page_count} pages</span>
            )}
            {size && <span className="doc-preview-size">{size}</span>}
          </div>

          <div className="doc-preview-actions">
            <a
              href={downloadUrl}
              className="doc-preview-action-btn"
              title="Download"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Download size={16} />
            </a>
            <div className="doc-preview-divider" />
            <button
              className="doc-preview-action-btn close"
              onClick={onClose}
              title="Close (Esc)"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* PDF viewer */}
        <div className="doc-preview-body">
          {loading && (
            <div className="doc-preview-loading">
              <Loader2 size={28} className="spinning" />
              <span>Loading document...</span>
            </div>
          )}
          {error && (
            <div className="doc-preview-error">
              <FileText size={32} strokeWidth={1} />
              <span>Could not load preview</span>
              <span className="doc-preview-error-detail">{error}</span>
            </div>
          )}
          {blobUrl && (
            <iframe
              src={blobUrl}
              className="doc-preview-iframe"
              title={`Preview: ${name}`}
            />
          )}
        </div>

        {/* Bottom bar */}
        <div className="doc-preview-bottombar">
          <span>Esc Close</span>
        </div>
      </div>
    </div>,
    document.body
  );
}

export default DocumentPreview;
