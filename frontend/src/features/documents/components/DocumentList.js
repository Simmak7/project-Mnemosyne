/**
 * DocumentList - Filterable list of document cards with grouping support
 */

import React from 'react';
import { Loader2 } from 'lucide-react';
import DocumentCard from './DocumentCard';

import './DocumentList.css';

const GROUP_LABELS = {
  pending: 'Pending',
  queued: 'Queued',
  processing: 'Processing',
  needs_review: 'Needs Review',
  completed: 'Completed',
  failed: 'Failed',
};

function DocumentList({ documents, groupedDocs, isLoading, error, selectedDocId, onSelect }) {
  if (isLoading) {
    return (
      <div className="document-list-loading">
        <Loader2 size={24} className="spinning" />
        <span>Loading documents...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="document-list-error">
        Failed to load documents: {error.message}
      </div>
    );
  }

  if (!documents || documents.length === 0) {
    return (
      <div className="document-list-empty">
        <p>No documents yet</p>
        <p className="document-list-hint">Upload PDFs via the Upload page</p>
      </div>
    );
  }

  // Grouped view
  if (groupedDocs) {
    const groupKeys = Object.keys(groupedDocs).sort();
    return (
      <div className="document-list">
        {groupKeys.map(group => (
          <div key={group} className="document-group">
            <div className="document-group-header">
              <span className="document-group-name">
                {GROUP_LABELS[group] || group}
              </span>
              <span className="document-group-count">
                {groupedDocs[group].length}
              </span>
            </div>
            {groupedDocs[group].map(doc => (
              <DocumentCard
                key={doc.id}
                document={doc}
                isSelected={doc.id === selectedDocId}
                onClick={() => onSelect(doc.id)}
              />
            ))}
          </div>
        ))}
      </div>
    );
  }

  // Flat view
  return (
    <div className="document-list">
      {documents.map(doc => (
        <DocumentCard
          key={doc.id}
          document={doc}
          isSelected={doc.id === selectedDocId}
          onClick={() => onSelect(doc.id)}
        />
      ))}
    </div>
  );
}

export default DocumentList;
