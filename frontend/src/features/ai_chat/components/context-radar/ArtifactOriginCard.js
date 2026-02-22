/**
 * ArtifactOriginCard - Shows the source image/document that generated a note
 *
 * Renders below a note preview when the note was created from an image
 * or PDF document analysis, showing a thumbnail or icon with filename.
 */
import React from 'react';
import { Camera, FileText, ExternalLink } from 'lucide-react';
import { API_URL } from '../../../../utils/api';

function ArtifactOriginCard({ citation, onNavigateToImage, onNavigateToNote }) {
  if (!citation) return null;

  const { origin_type, artifact_id, artifact_filename, artifact_url } = citation;

  // Only show for non-manual origins with an artifact
  if (!origin_type || origin_type === 'manual' || !artifact_id) return null;

  const isImage = origin_type === 'image_analysis';
  const isDocument = origin_type === 'document_analysis';
  if (!isImage && !isDocument) return null;

  const displayName = artifact_filename || (isImage ? `Image #${artifact_id}` : `Document #${artifact_id}`);

  const handleOpen = () => {
    if (isImage) {
      onNavigateToImage?.(artifact_id);
    } else if (isDocument) {
      // Navigate to document - use artifact_url or fallback
      window.location.hash = artifact_url || `/documents/${artifact_id}`;
    }
  };

  return (
    <div className={`artifact-origin-card ${isImage ? 'image' : 'document'}`}>
      <div className="artifact-origin-label">
        {isImage ? <Camera size={12} /> : <FileText size={12} />}
        <span>{isImage ? 'Generated from image' : 'Extracted from document'}</span>
      </div>
      <div className="artifact-origin-content">
        {isImage && (
          <div className="artifact-thumbnail">
            <img
              src={`${API_URL}/image/${artifact_id}`}
              alt={displayName}
            />
          </div>
        )}
        {isDocument && (
          <div className="artifact-doc-icon">
            <FileText size={24} />
          </div>
        )}
        <div className="artifact-origin-info">
          <span className="artifact-filename" title={displayName}>{displayName}</span>
          <button className="artifact-open-btn" onClick={handleOpen}>
            <ExternalLink size={12} />
            {isImage ? 'Open Image' : 'Open Document'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ArtifactOriginCard;
