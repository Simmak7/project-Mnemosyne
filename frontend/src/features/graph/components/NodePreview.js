import React from 'react';
import { format } from 'date-fns';
import './NodePreview.css';

/**
 * Hover preview tooltip for graph nodes
 *
 * Displays node metadata:
 * - Note: title, content snippet, tags, backlink count
 * - Tag: name, note count
 * - Image: filename, upload date, analysis status
 */
function NodePreview({ node, position }) {
  if (!node) return null;

  const formatDate = (dateString) => {
    try {
      return format(new Date(dateString), 'MMM dd, yyyy');
    } catch {
      return 'Unknown date';
    }
  };

  const getSnippet = (content, maxLength = 200) => {
    if (!content) return 'No content';
    const stripped = content.replace(/[#*`\[\]]/g, '').trim();
    return stripped.length > maxLength
      ? stripped.substring(0, maxLength) + '...'
      : stripped;
  };

  return (
    <div
      className="node-preview"
      style={{
        left: position.x,
        top: position.y,
      }}
    >
      {/* Header with node type indicator */}
      <div className={`preview-header ${node.type}`}>
        <span className="node-type-badge">
          {node.type === 'note' && '📝'}
          {node.type === 'tag' && '🏷️'}
          {node.type === 'image' && '🖼️'}
        </span>
        <h4 className="preview-title">{node.name}</h4>
      </div>

      {/* Content based on node type */}
      <div className="preview-content">
        {node.type === 'note' && (
          <>
            {node.content && (
              <p className="preview-snippet">{getSnippet(node.content)}</p>
            )}
            <div className="preview-meta">
              {node.created_at && (
                <span className="meta-item">
                  Created {formatDate(node.created_at)}
                </span>
              )}
              {node.tags && node.tags.length > 0 && (
                <div className="preview-tags">
                  {node.tags.slice(0, 3).map((tag, idx) => (
                    <span key={idx} className="tag-chip">
                      {tag}
                    </span>
                  ))}
                  {node.tags.length > 3 && (
                    <span className="tag-more">+{node.tags.length - 3}</span>
                  )}
                </div>
              )}
              {node.backlinkCount !== undefined && (
                <span className="meta-item">
                  {node.backlinkCount} backlink{node.backlinkCount !== 1 ? 's' : ''}
                </span>
              )}
            </div>
          </>
        )}

        {node.type === 'tag' && (
          <>
            <p className="preview-description">
              Tag used in {node.noteCount || 0} note{node.noteCount !== 1 ? 's' : ''}
            </p>
            {node.created_at && (
              <span className="meta-item">
                Created {formatDate(node.created_at)}
              </span>
            )}
          </>
        )}

        {node.type === 'image' && (
          <>
            {node.filename && (
              <p className="preview-filename">{node.filename}</p>
            )}
            <div className="preview-meta">
              {node.uploaded_at && (
                <span className="meta-item">
                  Uploaded {formatDate(node.uploaded_at)}
                </span>
              )}
              {node.ai_analysis_status && (
                <span className={`status-badge ${node.ai_analysis_status}`}>
                  {node.ai_analysis_status}
                </span>
              )}
            </div>
          </>
        )}
      </div>

      {/* Footer with interaction hint */}
      <div className="preview-footer">
        <span className="interaction-hint">Click to open</span>
      </div>
    </div>
  );
}

export default NodePreview;
