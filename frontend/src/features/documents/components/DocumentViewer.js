/**
 * DocumentViewer - Embedded PDF viewer
 * Opens the document's PDF in an iframe for inline viewing.
 */

import React from 'react';
import { FileText, ExternalLink } from 'lucide-react';
import { API_URL } from '../../../utils/api';

function DocumentViewer({ document }) {
  if (!document) return null;

  const pdfUrl = `${API_URL}/documents/${document.id}/file`;

  return (
    <div style={styles.container}>
      <div style={styles.toolbar}>
        <div style={styles.title}>
          <FileText size={16} />
          <span>{document.display_name || document.filename}</span>
        </div>
        <a
          href={pdfUrl}
          target="_blank"
          rel="noopener noreferrer"
          style={styles.openLink}
          title="Open in new tab"
        >
          <ExternalLink size={14} />
          Open
        </a>
      </div>
      <iframe
        src={pdfUrl}
        title={document.filename}
        style={styles.iframe}
      />
    </div>
  );
}

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    borderRadius: '8px',
    overflow: 'hidden',
    border: '1px solid rgba(255, 255, 255, 0.06)',
  },
  toolbar: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '8px 12px',
    background: 'rgba(255, 255, 255, 0.03)',
    borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
    flexShrink: 0,
  },
  title: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: '0.82rem',
    color: '#e4e4e7',
    fontWeight: 500,
    overflow: 'hidden',
    whiteSpace: 'nowrap',
    textOverflow: 'ellipsis',
  },
  openLink: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    fontSize: '0.75rem',
    color: '#a1a1aa',
    textDecoration: 'none',
    padding: '4px 8px',
    borderRadius: '4px',
    transition: 'all 0.15s',
    flexShrink: 0,
  },
  iframe: {
    flex: 1,
    width: '100%',
    border: 'none',
    background: '#1a1a1a',
  },
};

export default DocumentViewer;
