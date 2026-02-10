/**
 * Active Citations list - shows all citations from the latest response
 */
import React from 'react';
import { FileText, Image as ImageIcon } from 'lucide-react';

function ActiveCitationsList({ citations, selectedId, onSelect }) {
  if (!citations || citations.length === 0) return null;

  return (
    <div className="active-citations">
      <div className="active-citations-header">Sources ({citations.length})</div>
      <div className="active-citations-list">
        {citations.slice(0, 8).map((citation, idx) => (
          <button
            key={`${citation.source_type}-${citation.source_id}-${idx}`}
            className={`citation-item ${selectedId === citation.source_id ? 'selected' : ''} ${citation.source_type}`}
            onClick={() => onSelect(citation)}
            title={citation.title || `${citation.source_type} #${citation.source_id}`}
          >
            {citation.source_type?.startsWith('image') ? (
              <ImageIcon size={12} />
            ) : (
              <FileText size={12} />
            )}
            <span className="citation-title">
              {citation.title || `${citation.source_type} #${citation.source_id}`}
            </span>
            <span className="citation-score">
              {Math.round((citation.relevance_score || 0) * 100)}%
            </span>
          </button>
        ))}
        {citations.length > 8 && (
          <div className="citations-more">+{citations.length - 8} more</div>
        )}
      </div>
    </div>
  );
}

export default ActiveCitationsList;
