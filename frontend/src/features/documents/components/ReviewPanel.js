/**
 * ReviewPanel - AI suggestions review with approve/skip actions
 * Shows editable summary, tag checkboxes, wikilink checkboxes.
 * Includes extraction info and cross-navigation to notes.
 */

import React, { useState } from 'react';
import {
  CheckCircle, XCircle, FileText, Clock,
  AlertCircle, Loader2, RefreshCw, Download, Eye,
  ArrowRight, Type, Scan, FileDown, BookOpen, FolderPlus,
} from 'lucide-react';
import DocCollectionPicker from './DocCollectionPicker';
import DocumentPreview from './DocumentPreview';
import { useDocumentReview } from '../hooks/useDocumentReview';
import {
  useApproveDocument, useRejectDocument,
  useRetryDocument, useExtractToNote,
} from '../hooks/useDocuments';
import { API_URL } from '../../../utils/api';

import './ReviewPanel.css';

function ReviewPanel({ document, onNavigateToNote }) {
  const review = useDocumentReview(document);
  const approveMutation = useApproveDocument();
  const rejectMutation = useRejectDocument();
  const retryMutation = useRetryDocument();
  const extractMutation = useExtractToNote();

  if (!document) {
    return (
      <div className="review-panel-empty">
        <FileText size={40} strokeWidth={1} />
        <p>Select a document to view details</p>
      </div>
    );
  }

  const status = document.ai_analysis_status;
  const isReviewable = status === 'needs_review';
  const isProcessing = status === 'processing' || status === 'queued';
  const isFailed = status === 'failed';
  const isCompleted = status === 'completed';
  const isPending = status === 'pending';
  const suggestedTags = document.suggested_tags || [];
  const suggestedWikilinks = document.suggested_wikilinks || [];
  const textLength = document.extracted_text_length || 0;
  const textAlreadyAppended = document.text_appended_to_note || extractMutation.isSuccess;

  const handleApprove = () => {
    approveMutation.mutate({ docId: document.id, data: review.getApprovalPayload() });
  };

  const handleReject = () => rejectMutation.mutate(document.id);
  const handleRetry = () => retryMutation.mutate(document.id);

  const handleReanalyze = () => {
    const confirmed = window.confirm(
      'Re-analyze this document?\n\n' +
      'This will discard all current AI suggestions and re-run analysis from scratch. ' +
      'If a summary note was already created, it will NOT be updated automatically \u2014 ' +
      'you will need to approve the new results to create a new note.'
    );
    if (confirmed) retryMutation.mutate(document.id);
  };

  const handleExtractText = () => {
    if (textLength > 100000) {
      const confirmed = window.confirm(
        `The extracted text is ${(textLength / 1000).toFixed(0)}k characters.\n\n` +
        'Adding very large texts to a note may affect performance. Continue?'
      );
      if (!confirmed) return;
    }
    extractMutation.mutate(document.id);
  };

  return (
    <div className="review-panel">
      <ReviewHeader document={document} />
      <ExtractionInfo document={document} />


      {isProcessing && <ProcessingState />}
      {isPending && <PendingState />}
      {isFailed && <FailedState onRetry={handleRetry} isRetrying={retryMutation.isPending} />}

      {(isReviewable || isCompleted) && (
        <>
          <SummarySection
            title={review.summaryTitle}
            content={review.summaryContent}
            onTitleChange={review.setSummaryTitle}
            onContentChange={review.setSummaryContent}
            readOnly={isCompleted}
          />

          {suggestedTags.length > 0 && (
            <CheckboxSection
              label="Tags"
              items={suggestedTags}
              checked={review.checkedTags}
              onToggle={review.toggleTag}
              readOnly={isCompleted}
            />
          )}

          {suggestedWikilinks.length > 0 && (
            <CheckboxSection
              label="Wikilinks"
              items={suggestedWikilinks}
              checked={review.checkedWikilinks}
              onToggle={review.toggleWikilink}
              readOnly={isCompleted}
            />
          )}

          {isReviewable && (
            <div className="review-actions">
              <button
                className="review-btn review-btn-approve"
                onClick={handleApprove}
                disabled={approveMutation.isPending}
              >
                <CheckCircle size={16} />
                {approveMutation.isPending ? 'Creating Note...' : 'Approve & Create Note'}
              </button>
              <button
                className="review-btn review-btn-skip"
                onClick={handleReject}
                disabled={rejectMutation.isPending}
              >
                <XCircle size={16} />
                Skip
              </button>
            </div>
          )}

          {/* Completed actions: note link + extract text */}
          {isCompleted && document.summary_note_id && (
            <div className="review-completed-actions">
              <button
                className="review-action-card review-action-card--note"
                onClick={() => onNavigateToNote && onNavigateToNote(document.summary_note_id)}
              >
                <div className="review-action-card-icon">
                  <BookOpen size={18} />
                </div>
                <div className="review-action-card-content">
                  <span className="review-action-card-title">Open Summary Note</span>
                  <span className="review-action-card-sub">View in Notes section</span>
                </div>
                <ArrowRight size={16} className="review-action-card-arrow" />
              </button>

              {textLength > 0 && (
                <button
                  className="review-action-card review-action-card--extract"
                  onClick={handleExtractText}
                  disabled={extractMutation.isPending || textAlreadyAppended}
                >
                  <div className="review-action-card-icon">
                    {extractMutation.isPending
                      ? <Loader2 size={18} className="spinning" />
                      : textAlreadyAppended
                        ? <CheckCircle size={18} />
                        : <FileDown size={18} />}
                  </div>
                  <div className="review-action-card-content">
                    <span className="review-action-card-title">
                      {extractMutation.isPending ? 'Adding...'
                        : textAlreadyAppended ? 'Text Added to Note'
                        : 'Add Full Text to Note'}
                    </span>
                    <span className="review-action-card-sub">
                      {textLength > 1000
                        ? `${(textLength / 1000).toFixed(1)}k characters`
                        : `${textLength} characters`}
                    </span>
                  </div>
                </button>
              )}
            </div>
          )}

          {(isReviewable || isCompleted) && (
            <button
              className="review-reanalyze-link"
              onClick={handleReanalyze}
              disabled={retryMutation.isPending}
            >
              <RefreshCw size={13} className={retryMutation.isPending ? 'spinning' : ''} />
              {retryMutation.isPending ? 'Re-analyzing...' : 'Re-analyze document'}
            </button>
          )}
        </>
      )}
    </div>
  );
}

function ReviewHeader({ document }) {
  const [showPreview, setShowPreview] = useState(false);
  const name = document.display_name || document.filename;
  const size = document.file_size
    ? `${(document.file_size / (1024 * 1024)).toFixed(1)}MB`
    : '';

  return (
    <div className="review-header">
      {document.thumbnail_path ? (
        <img
          src={`${API_URL}/documents/${document.id}/thumbnail`}
          alt=""
          className="review-header-thumb"
        />
      ) : (
        <div className="review-header-icon"><FileText size={32} strokeWidth={1.2} /></div>
      )}
      <div className="review-header-info">
        <h3 className="review-header-name" title={name}>{name}</h3>
        <div className="review-header-meta">
          {document.page_count && <span>{document.page_count} pages</span>}
          {size && <span>{size}</span>}
          {document.document_type && document.document_type !== 'unknown' && (
            <span>{document.document_type}</span>
          )}
        </div>
      </div>
      <div className="review-header-actions">
        <DocCollectionPicker documentId={document.id} />
        <button
          className="review-header-action"
          onClick={() => setShowPreview(true)}
          title="Preview document"
        >
          <Eye size={16} />
        </button>
        <a
          href={`${API_URL}/documents/${document.id}/file`}
          target="_blank"
          rel="noopener noreferrer"
          className="review-header-action"
          title="Download"
        >
          <Download size={16} />
        </a>
      </div>

      {showPreview && (
        <DocumentPreview
          document={document}
          onClose={() => setShowPreview(false)}
        />
      )}
    </div>
  );
}

function ExtractionInfo({ document }) {
  const { extraction_method, extracted_text_length } = document;
  if (!extraction_method && !extracted_text_length) return null;

  const method = extraction_method === 'vision_ocr' ? 'Vision OCR' : 'Text extraction';
  const MethodIcon = extraction_method === 'vision_ocr' ? Scan : Type;
  const textLen = extracted_text_length
    ? extracted_text_length > 1000
      ? `${(extracted_text_length / 1000).toFixed(1)}k chars`
      : `${extracted_text_length} chars`
    : null;

  return (
    <div className="review-extraction-info">
      <MethodIcon size={12} />
      <span>{method}</span>
      {textLen && <span className="review-extraction-length">{textLen}</span>}
    </div>
  );
}

function SummarySection({ title, content, onTitleChange, onContentChange, readOnly }) {
  return (
    <div className="review-section">
      <label className="review-label">AI Summary</label>
      <input
        type="text"
        className="review-input"
        value={title}
        onChange={e => onTitleChange(e.target.value)}
        readOnly={readOnly}
        placeholder="Summary title"
      />
      <textarea
        className="review-textarea"
        value={content}
        onChange={e => onContentChange(e.target.value)}
        readOnly={readOnly}
        rows={6}
        placeholder="AI-generated summary..."
      />
    </div>
  );
}

function CheckboxSection({ label, items, checked, onToggle, readOnly }) {
  return (
    <div className="review-section">
      <label className="review-label">{label}</label>
      <div className="review-checkbox-list">
        {items.map(item => (
          <label key={item} className="review-checkbox">
            <input
              type="checkbox"
              checked={checked.includes(item)}
              onChange={() => onToggle(item)}
              disabled={readOnly}
            />
            <span>{item}</span>
          </label>
        ))}
      </div>
    </div>
  );
}

function ProcessingState() {
  return (
    <div className="review-status-block">
      <Loader2 size={24} className="spinning" />
      <p>Analyzing document...</p>
      <p className="review-status-hint">Extracting text and generating AI summary</p>
    </div>
  );
}

function PendingState() {
  return (
    <div className="review-status-block">
      <Clock size={24} />
      <p>Waiting to process</p>
    </div>
  );
}

function FailedState({ onRetry, isRetrying }) {
  return (
    <div className="review-status-block review-status-failed">
      <AlertCircle size={24} />
      <p>Analysis failed</p>
      <button className="review-btn review-btn-retry" onClick={onRetry} disabled={isRetrying}>
        <RefreshCw size={14} className={isRetrying ? 'spinning' : ''} />
        {isRetrying ? 'Retrying...' : 'Retry Analysis'}
      </button>
    </div>
  );
}

export default ReviewPanel;
