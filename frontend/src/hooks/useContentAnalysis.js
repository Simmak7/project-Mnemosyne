import { useState, useEffect, useMemo, useCallback } from 'react';
import debounce from 'lodash.debounce';

/**
 * useContentAnalysis - Debounced content analysis for Tiptap editor
 *
 * Analyzes editor content to extract:
 * - Wikilinks: [[Note Title]]
 * - Hashtags: #tag
 * - Word count
 * - Character count
 * - Plain text
 * - HTML content
 *
 * Uses 500ms debounce to avoid excessive re-renders during typing.
 *
 * @param {Object} editor - Tiptap editor instance
 * @param {string} noteTitle - Current note title
 * @returns {Object} Analyzed content data
 */
export function useContentAnalysis(editor, noteTitle = '') {
  const [analysisData, setAnalysisData] = useState({
    wikilinks: [],
    hashtags: [],
    wordCount: 0,
    charCount: 0,
    plainText: '',
    htmlContent: '',
    noteTitle: '',
  });

  // Debounced analysis function
  const analyzeContent = useCallback(
    debounce((editorInstance, title) => {
      if (!editorInstance) {
        setAnalysisData({
          wikilinks: [],
          hashtags: [],
          wordCount: 0,
          charCount: 0,
          plainText: '',
          htmlContent: '',
          noteTitle: title,
        });
        return;
      }

      try {
        const htmlContent = editorInstance.getHTML();
        const plainText = editorInstance.getText();

        // Extract wikilinks from HTML attributes
        const wikilinkMatches = htmlContent.matchAll(/data-wikilink-title="([^"]+)"/g);
        const wikilinks = [...new Set([...wikilinkMatches].map(match => match[1]))];

        // Extract hashtags from HTML attributes
        const hashtagMatches = htmlContent.matchAll(/data-hashtag="([^"]+)"/g);
        const hashtags = [...new Set([...hashtagMatches].map(match => match[1]))];

        // Calculate word and character counts
        const wordCount = plainText.trim().split(/\s+/).filter(word => word.length > 0).length;
        const charCount = plainText.length;

        setAnalysisData({
          wikilinks,
          hashtags,
          wordCount,
          charCount,
          plainText,
          htmlContent,
          noteTitle: title,
        });
      } catch (error) {
        if (process.env.NODE_ENV === 'development') {
          console.error('Error analyzing content:', error);
        }
      }
    }, 500), // 500ms debounce
    []
  );

  // Listen to editor updates
  useEffect(() => {
    if (!editor) return;

    const updateHandler = () => {
      analyzeContent(editor, noteTitle);
    };

    // Initial analysis
    analyzeContent(editor, noteTitle);

    // Listen to editor updates
    editor.on('update', updateHandler);

    return () => {
      editor.off('update', updateHandler);
      analyzeContent.cancel(); // Cancel pending debounced calls
    };
  }, [editor, noteTitle, analyzeContent]);

  // Also update when title changes
  useEffect(() => {
    if (editor) {
      analyzeContent(editor, noteTitle);
    }
  }, [noteTitle, editor, analyzeContent]);

  return analysisData;
}

/**
 * useInstantContentAnalysis - Non-debounced content analysis for immediate stats
 *
 * Use this for simple stats that don't need debouncing (word/char count displays)
 *
 * @param {Object} editor - Tiptap editor instance
 * @returns {Object} Instant content stats
 */
export function useInstantContentAnalysis(editor) {
  const [stats, setStats] = useState({
    wordCount: 0,
    charCount: 0,
  });

  useEffect(() => {
    if (!editor) {
      setStats({ wordCount: 0, charCount: 0 });
      return;
    }

    const updateStats = () => {
      const plainText = editor.getText();
      const wordCount = plainText.trim().split(/\s+/).filter(word => word.length > 0).length;
      const charCount = plainText.length;

      setStats({ wordCount, charCount });
    };

    // Initial calculation
    updateStats();

    // Listen to editor updates
    editor.on('update', updateStats);

    return () => {
      editor.off('update', updateStats);
    };
  }, [editor]);

  return stats;
}

/**
 * extractWikilinksFromHTML - Extract wikilink titles from HTML string
 * @param {string} html - HTML content with wikilink data attributes
 * @returns {Array<string>} Array of wikilink titles
 */
export function extractWikilinksFromHTML(html) {
  if (!html) return [];
  const matches = html.matchAll(/data-wikilink-title="([^"]+)"/g);
  return [...new Set([...matches].map(match => match[1]))];
}

/**
 * extractHashtagsFromHTML - Extract hashtags from HTML string
 * @param {string} html - HTML content with hashtag data attributes
 * @returns {Array<string>} Array of hashtag names
 */
export function extractHashtagsFromHTML(html) {
  if (!html) return [];
  const matches = html.matchAll(/data-hashtag="([^"]+)"/g);
  return [...new Set([...matches].map(match => match[1]))];
}

export default useContentAnalysis;
