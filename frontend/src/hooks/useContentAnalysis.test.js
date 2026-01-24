/**
 * Unit tests for useContentAnalysis hook
 * Tests wikilink and hashtag extraction from HTML
 */

import {
  extractWikilinksFromHTML,
  extractHashtagsFromHTML,
} from './useContentAnalysis';

describe('useContentAnalysis', () => {
  describe('extractWikilinksFromHTML', () => {
    it('should extract single wikilink from HTML', () => {
      const html = '<span data-wikilink-title="Test Note">Test Note</span>';
      const wikilinks = extractWikilinksFromHTML(html);

      expect(wikilinks).toHaveLength(1);
      expect(wikilinks[0]).toBe('Test Note');
    });

    it('should extract multiple wikilinks from HTML', () => {
      const html = `
        <span data-wikilink-title="First Note">First Note</span>
        <span data-wikilink-title="Second Note">Second Note</span>
        <span data-wikilink-title="Third Note">Third Note</span>
      `;
      const wikilinks = extractWikilinksFromHTML(html);

      expect(wikilinks).toHaveLength(3);
      expect(wikilinks).toContain('First Note');
      expect(wikilinks).toContain('Second Note');
      expect(wikilinks).toContain('Third Note');
    });

    it('should deduplicate identical wikilinks', () => {
      const html = `
        <span data-wikilink-title="Test Note">Test Note</span>
        <span data-wikilink-title="Test Note">Test Note</span>
      `;
      const wikilinks = extractWikilinksFromHTML(html);

      expect(wikilinks).toHaveLength(1);
      expect(wikilinks[0]).toBe('Test Note');
    });

    it('should handle wikilinks with special characters', () => {
      const html = '<span data-wikilink-title="Note with &quot;Quotes&quot;">Note</span>';
      const wikilinks = extractWikilinksFromHTML(html);

      expect(wikilinks).toHaveLength(1);
      expect(wikilinks[0]).toBe('Note with &quot;Quotes&quot;');
    });

    it('should handle wikilinks with spaces and punctuation', () => {
      const html = '<span data-wikilink-title="My Note: A Title!">My Note: A Title!</span>';
      const wikilinks = extractWikilinksFromHTML(html);

      expect(wikilinks).toHaveLength(1);
      expect(wikilinks[0]).toBe('My Note: A Title!');
    });

    it('should return empty array when no wikilinks', () => {
      const html = '<p>Just plain text</p>';
      const wikilinks = extractWikilinksFromHTML(html);

      expect(wikilinks).toHaveLength(0);
    });

    it('should return empty array for empty HTML', () => {
      const wikilinks = extractWikilinksFromHTML('');
      expect(wikilinks).toHaveLength(0);
    });

    it('should return empty array for null/undefined', () => {
      expect(extractWikilinksFromHTML(null)).toHaveLength(0);
      expect(extractWikilinksFromHTML(undefined)).toHaveLength(0);
    });

    it('should handle mixed content (wikilinks + regular text)', () => {
      const html = `
        <p>This is a note about <span data-wikilink-title="JavaScript">JavaScript</span> and
        <span data-wikilink-title="Python">Python</span> programming.</p>
      `;
      const wikilinks = extractWikilinksFromHTML(html);

      expect(wikilinks).toHaveLength(2);
      expect(wikilinks).toContain('JavaScript');
      expect(wikilinks).toContain('Python');
    });
  });

  describe('extractHashtagsFromHTML', () => {
    it('should extract single hashtag from HTML', () => {
      const html = '<span data-hashtag="programming">programming</span>';
      const hashtags = extractHashtagsFromHTML(html);

      expect(hashtags).toHaveLength(1);
      expect(hashtags[0]).toBe('programming');
    });

    it('should extract multiple hashtags from HTML', () => {
      const html = `
        <span data-hashtag="javascript">javascript</span>
        <span data-hashtag="react">react</span>
        <span data-hashtag="testing">testing</span>
      `;
      const hashtags = extractHashtagsFromHTML(html);

      expect(hashtags).toHaveLength(3);
      expect(hashtags).toContain('javascript');
      expect(hashtags).toContain('react');
      expect(hashtags).toContain('testing');
    });

    it('should deduplicate identical hashtags', () => {
      const html = `
        <span data-hashtag="important">important</span>
        <span data-hashtag="important">important</span>
      `;
      const hashtags = extractHashtagsFromHTML(html);

      expect(hashtags).toHaveLength(1);
      expect(hashtags[0]).toBe('important');
    });

    it('should handle hashtags with hyphens', () => {
      const html = '<span data-hashtag="web-development">web-development</span>';
      const hashtags = extractHashtagsFromHTML(html);

      expect(hashtags).toHaveLength(1);
      expect(hashtags[0]).toBe('web-development');
    });

    it('should handle hashtags with underscores', () => {
      const html = '<span data-hashtag="code_review">code_review</span>';
      const hashtags = extractHashtagsFromHTML(html);

      expect(hashtags).toHaveLength(1);
      expect(hashtags[0]).toBe('code_review');
    });

    it('should handle hashtags with numbers', () => {
      const html = '<span data-hashtag="phase6">phase6</span>';
      const hashtags = extractHashtagsFromHTML(html);

      expect(hashtags).toHaveLength(1);
      expect(hashtags[0]).toBe('phase6');
    });

    it('should return empty array when no hashtags', () => {
      const html = '<p>Just plain text</p>';
      const hashtags = extractHashtagsFromHTML(html);

      expect(hashtags).toHaveLength(0);
    });

    it('should return empty array for empty HTML', () => {
      const hashtags = extractHashtagsFromHTML('');
      expect(hashtags).toHaveLength(0);
    });

    it('should return empty array for null/undefined', () => {
      expect(extractHashtagsFromHTML(null)).toHaveLength(0);
      expect(extractHashtagsFromHTML(undefined)).toHaveLength(0);
    });

    it('should handle mixed content (hashtags + regular text)', () => {
      const html = `
        <p>This note is tagged with
        <span data-hashtag="urgent">urgent</span> and
        <span data-hashtag="work">work</span>.</p>
      `;
      const hashtags = extractHashtagsFromHTML(html);

      expect(hashtags).toHaveLength(2);
      expect(hashtags).toContain('urgent');
      expect(hashtags).toContain('work');
    });
  });

  describe('Combined wikilinks and hashtags', () => {
    it('should extract both wikilinks and hashtags from same HTML', () => {
      const html = `
        <p>See <span data-wikilink-title="Related Note">Related Note</span>
        and check <span data-hashtag="important">important</span> items.</p>
      `;

      const wikilinks = extractWikilinksFromHTML(html);
      const hashtags = extractHashtagsFromHTML(html);

      expect(wikilinks).toHaveLength(1);
      expect(wikilinks[0]).toBe('Related Note');

      expect(hashtags).toHaveLength(1);
      expect(hashtags[0]).toBe('important');
    });

    it('should handle multiple of both types', () => {
      const html = `
        <span data-wikilink-title="Note 1">Note 1</span>
        <span data-hashtag="tag1">tag1</span>
        <span data-wikilink-title="Note 2">Note 2</span>
        <span data-hashtag="tag2">tag2</span>
      `;

      const wikilinks = extractWikilinksFromHTML(html);
      const hashtags = extractHashtagsFromHTML(html);

      expect(wikilinks).toHaveLength(2);
      expect(hashtags).toHaveLength(2);
    });
  });

  describe('Edge cases', () => {
    it('should handle malformed HTML gracefully', () => {
      const html = '<span data-wikilink-title="Test">Unclosed tag';
      const wikilinks = extractWikilinksFromHTML(html);

      expect(wikilinks).toHaveLength(1);
      expect(wikilinks[0]).toBe('Test');
    });

    it('should handle HTML with nested tags', () => {
      const html = `
        <div>
          <p>
            <span data-wikilink-title="Nested Note">
              <strong>Nested Note</strong>
            </span>
          </p>
        </div>
      `;
      const wikilinks = extractWikilinksFromHTML(html);

      expect(wikilinks).toHaveLength(1);
      expect(wikilinks[0]).toBe('Nested Note');
    });

    it('should handle very long HTML strings', () => {
      const longHTML = '<p>Start</p>' +
        '<span data-wikilink-title="Note 1">Note 1</span>'.repeat(100) +
        '<p>End</p>';

      const wikilinks = extractWikilinksFromHTML(longHTML);

      // Should deduplicate to 1 unique wikilink
      expect(wikilinks).toHaveLength(1);
      expect(wikilinks[0]).toBe('Note 1');
    });

    it('should handle empty data attributes', () => {
      const html = '<span data-wikilink-title="">Empty</span>';
      const wikilinks = extractWikilinksFromHTML(html);

      // Empty attributes won't match regex ([^"]+) requires at least 1 char
      expect(wikilinks).toHaveLength(0);
    });

    it('should handle unicode characters in titles', () => {
      const html = '<span data-wikilink-title="测试笔记">测试笔记</span>';
      const wikilinks = extractWikilinksFromHTML(html);

      expect(wikilinks).toHaveLength(1);
      expect(wikilinks[0]).toBe('测试笔记');
    });

    it('should handle emoji in hashtags', () => {
      const html = '<span data-hashtag="important🔥">important🔥</span>';
      const hashtags = extractHashtagsFromHTML(html);

      expect(hashtags).toHaveLength(1);
      expect(hashtags[0]).toBe('important🔥');
    });
  });
});
