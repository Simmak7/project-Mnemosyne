/**
 * Preview section - shows note/image details when citation is clicked
 */
import React, { useState, useEffect } from 'react';
import { FileText, Image as ImageIcon, ExternalLink, X } from 'lucide-react';
import ActiveCitationsList from './ActiveCitationsList';

function PreviewSection({ previewItem, activeCitations, onNavigateToNote, onNavigateToImage, onClear, onSelectCitation }) {
  const [noteData, setNoteData] = useState(null);
  const [imageData, setImageData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Fetch preview data when item changes
  useEffect(() => {
    if (!previewItem) {
      setNoteData(null);
      setImageData(null);
      return;
    }

    async function fetchData() {
      setIsLoading(true);
      try {
        const token = localStorage.getItem('token');
        const headers = {
          'Authorization': token ? `Bearer ${token}` : '',
        };

        const isImageType = previewItem.type?.startsWith('image');

        if (!isImageType && (previewItem.type === 'note' || previewItem.type === 'chunk')) {
          const response = await fetch(
            `http://localhost:8000/notes/${previewItem.id}`,
            { headers }
          );
          if (response.ok) {
            const data = await response.json();
            setNoteData(data);
            setImageData(null);
          }
        } else if (isImageType) {
          const response = await fetch(
            `http://localhost:8000/images/${previewItem.id}`,
            { headers }
          );
          if (response.ok) {
            const data = await response.json();
            setImageData(data);
            setNoteData(null);
          }
        }
      } catch (error) {
        console.error('Failed to fetch preview:', error);
      } finally {
        setIsLoading(false);
      }
    }

    fetchData();
  }, [previewItem]);

  if (!previewItem) {
    return (
      <div className="preview-section empty">
        <ActiveCitationsList
          citations={activeCitations}
          selectedId={null}
          onSelect={onSelectCitation}
        />
        {(!activeCitations || activeCitations.length === 0) && (
          <div className="preview-empty">
            <FileText size={24} />
            <span>Click a citation to preview</span>
          </div>
        )}
      </div>
    );
  }

  const isImageType = previewItem?.type?.startsWith('image');

  const handleNavigate = () => {
    if (!isImageType && (previewItem.type === 'note' || previewItem.type === 'chunk')) {
      onNavigateToNote?.(previewItem.id);
    } else if (isImageType) {
      onNavigateToImage?.(previewItem.id);
    }
  };

  return (
    <div className="preview-section">
      <div className="preview-header">
        <div className="preview-type">
          {isImageType ? (
            <ImageIcon size={14} className="image-icon" />
          ) : (
            <FileText size={14} className="note-icon" />
          )}
          <span>{isImageType ? 'Image' : 'Note'}</span>
        </div>
        <button className="preview-close" onClick={onClear}>
          <X size={14} />
        </button>
      </div>

      {isLoading ? (
        <div className="preview-loading">Loading...</div>
      ) : noteData ? (
        <div className="preview-content">
          <h4 className="preview-title">{noteData.title || 'Untitled'}</h4>
          <div className="preview-text">
            {noteData.content?.substring(0, 300)}
            {noteData.content?.length > 300 && '...'}
          </div>
          {previewItem.citation && (
            <div className="preview-meta">
              <span className="meta-item">
                Relevance: {Math.round((previewItem.citation.relevance_score || 0) * 100)}%
              </span>
              <span className="meta-item">
                Method: {previewItem.citation.retrieval_method}
              </span>
            </div>
          )}
          <button className="preview-navigate" onClick={handleNavigate}>
            <ExternalLink size={14} />
            Open Note
          </button>
        </div>
      ) : imageData ? (
        <div className="preview-content image">
          <div className="preview-image-wrapper">
            <img
              src={`http://localhost:8000/image/${imageData.id}`}
              alt={imageData.filename || 'Image'}
            />
          </div>
          <h4 className="preview-title">{imageData.display_name || imageData.filename || 'Image'}</h4>
          {imageData.ai_analysis_result && (
            <div className="preview-text">
              {imageData.ai_analysis_result.substring(0, 200)}
              {imageData.ai_analysis_result.length > 200 && '...'}
            </div>
          )}
          <button className="preview-navigate" onClick={handleNavigate}>
            <ExternalLink size={14} />
            Open Image
          </button>
        </div>
      ) : (
        <div className="preview-loading">Failed to load preview</div>
      )}

      <ActiveCitationsList
        citations={activeCitations}
        selectedId={previewItem?.id}
        onSelect={onSelectCitation}
      />
    </div>
  );
}

export default PreviewSection;
