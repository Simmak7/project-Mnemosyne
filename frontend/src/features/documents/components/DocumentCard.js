/**
 * DocumentCard - Single document in the list
 * Shows thumbnail, filename, type badge, page count, extraction badge, status
 */

import React from 'react';
import { FileText, Clock, CheckCircle, AlertCircle, Eye, Loader2, Scan, Type } from 'lucide-react';
import { API_URL } from '../../../utils/api';

import './DocumentCard.css';

const STATUS_CONFIG = {
  pending: { icon: Clock, color: '#71717a', label: 'Pending' },
  queued: { icon: Clock, color: '#71717a', label: 'Queued' },
  processing: { icon: Loader2, color: '#818cf8', label: 'Processing' },
  needs_review: { icon: Eye, color: '#fbbf24', label: 'Needs Review' },
  completed: { icon: CheckCircle, color: '#34d399', label: 'Completed' },
  failed: { icon: AlertCircle, color: '#ef4444', label: 'Failed' },
};

function DocumentCard({ document, isSelected, onClick }) {
  const { display_name, filename, page_count, ai_analysis_status, file_size, extraction_method, document_type } = document;
  const name = display_name || filename;
  const status = STATUS_CONFIG[ai_analysis_status] || STATUS_CONFIG.pending;
  const StatusIcon = status.icon;
  const isProcessing = ai_analysis_status === 'processing';

  const formattedSize = file_size
    ? `${(file_size / (1024 * 1024)).toFixed(1)}MB`
    : '';

  return (
    <button
      className={`document-card ng-glass-interactive ${isSelected ? 'selected' : ''}`}
      onClick={onClick}
    >
      {/* Thumbnail or icon */}
      <div className="document-card-thumb">
        {document.thumbnail_path ? (
          <img
            src={`${API_URL}/documents/${document.id}/thumbnail`}
            alt=""
            className="document-card-thumb-img"
            loading="lazy"
          />
        ) : (
          <FileText size={28} strokeWidth={1.2} />
        )}
      </div>

      {/* Info */}
      <div className="document-card-info">
        <div className="document-card-name" title={name}>{name}</div>
        <div className="document-card-meta">
          {page_count && <span>{page_count}p</span>}
          {formattedSize && <span>{formattedSize}</span>}
          {document_type && document_type !== 'unknown' && (
            <span className="document-card-type">{document_type}</span>
          )}
          {extraction_method && (
            <span className="document-card-extraction" title={`Extracted via ${extraction_method}`}>
              {extraction_method === 'vision_ocr' ? <Scan size={10} /> : <Type size={10} />}
            </span>
          )}
          <span className="document-card-status" style={{ color: status.color }}>
            <StatusIcon size={12} className={isProcessing ? 'spinning' : ''} />
            {status.label}
          </span>
        </div>
      </div>
    </button>
  );
}

export default DocumentCard;
