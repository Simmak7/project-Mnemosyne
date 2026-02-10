/**
 * useDocumentReview Hook
 * Local state management for the review panel.
 */

import { useState, useEffect, useCallback } from 'react';

/**
 * Manages review state: checked tags, wikilinks, edited summary.
 *
 * @param {object} document - Document object from API
 * @returns {object} Review state and actions
 */
export function useDocumentReview(document) {
  const [checkedTags, setCheckedTags] = useState([]);
  const [checkedWikilinks, setCheckedWikilinks] = useState([]);
  const [summaryTitle, setSummaryTitle] = useState('');
  const [summaryContent, setSummaryContent] = useState('');

  // Initialize from document suggestions when document changes
  useEffect(() => {
    if (document) {
      setCheckedTags(document.suggested_tags || []);
      setCheckedWikilinks(document.suggested_wikilinks || []);
      setSummaryTitle(buildTitle(document));
      setSummaryContent(document.ai_summary || '');
    }
  }, [document?.id, document?.ai_summary]);

  const toggleTag = useCallback((tag) => {
    setCheckedTags(prev =>
      prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]
    );
  }, []);

  const toggleWikilink = useCallback((wikilink) => {
    setCheckedWikilinks(prev =>
      prev.includes(wikilink) ? prev.filter(w => w !== wikilink) : [...prev, wikilink]
    );
  }, []);

  const getApprovalPayload = useCallback(() => ({
    approved_tags: checkedTags,
    approved_wikilinks: checkedWikilinks,
    summary_title: summaryTitle,
    summary_content: summaryContent,
  }), [checkedTags, checkedWikilinks, summaryTitle, summaryContent]);

  return {
    checkedTags,
    checkedWikilinks,
    summaryTitle,
    summaryContent,
    setSummaryTitle,
    setSummaryContent,
    toggleTag,
    toggleWikilink,
    getApprovalPayload,
  };
}

function buildTitle(doc) {
  const name = doc.display_name || doc.filename || 'Document';
  const clean = name.includes('.') ? name.split('.').slice(0, -1).join('.') : name;
  return clean;
}
