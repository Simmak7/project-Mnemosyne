import React from 'react';
import DOMPurify from 'dompurify';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './NoteContentRenderer.css';

/**
 * NoteContentRenderer - Renders note content with proper formatting
 *
 * If html_content is available (from TipTap editor), renders sanitized HTML.
 * Otherwise falls back to Markdown rendering.
 *
 * @param {Object} props
 * @param {string} props.content - Plain text/markdown content
 * @param {string} props.htmlContent - HTML content from TipTap editor
 * @param {string} props.className - Additional CSS class
 * @param {Function} props.onWikilinkClick - Handler for wikilink clicks
 * @param {Function} props.onHashtagClick - Handler for hashtag clicks
 * @param {Function} props.onCheckboxToggle - Handler for checkbox toggle (lineText, checked)
 */
function NoteContentRenderer({
  content,
  htmlContent,
  className = '',
  onWikilinkClick,
  onHashtagClick,
  onCheckboxToggle
}) {
  // Configure DOMPurify to allow TipTap's data attributes
  const sanitizeConfig = {
    ADD_ATTR: ['data-type', 'data-checked', 'data-wikilink-title', 'data-wikilink-alias', 'data-hashtag', 'contenteditable'],
    ADD_TAGS: ['wikilink', 'hashtag'],
    ALLOW_DATA_ATTR: true,
  };

  // Convert plain text [[wikilinks]] to proper span elements
  const convertWikilinks = (html) => {
    // Match [[Title]] or [[Title|Alias]] patterns not already converted
    return html.replace(
      /(?<!data-wikilink-title="[^"]*)\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g,
      (match, title, alias) => {
        const displayText = alias || title;
        const aliasAttr = alias ? ` data-wikilink-alias="${alias}"` : '';
        return `<span data-wikilink-title="${title}"${aliasAttr} class="wikilink-chip" style="cursor:pointer;color:#60a5fa;text-decoration:underline;">[[${displayText}]]</span>`;
      }
    );
  };

  // Convert plain text #hashtags to proper span elements
  const convertHashtags = (html) => {
    // Match #tag patterns not already converted
    return html.replace(
      /(?<!data-hashtag="|class="|>)#([a-zA-Z][a-zA-Z0-9_-]*)/g,
      (match, tag) => {
        return `<span data-hashtag="${tag}" class="hashtag-chip" style="cursor:pointer;color:#fbbf24;">#${tag}</span>`;
      }
    );
  };

  // Process HTML content to convert plain text wikilinks and hashtags
  const processHtmlContent = (html) => {
    if (!html) return html;
    let processed = html;
    processed = convertWikilinks(processed);
    processed = convertHashtags(processed);
    return processed;
  };

  // Handle clicks on wikilinks and hashtags in HTML content
  const handleContentClick = (e) => {
    const target = e.target;

    // Check for wikilink click
    if (target.hasAttribute('data-wikilink-title')) {
      e.preventDefault();
      const title = target.getAttribute('data-wikilink-title');
      if (onWikilinkClick) {
        onWikilinkClick(title);
      }
    }

    // Check for hashtag click
    if (target.hasAttribute('data-hashtag')) {
      e.preventDefault();
      const tag = target.getAttribute('data-hashtag');
      if (onHashtagClick) {
        onHashtagClick(tag);
      }
    }
  };

  // If HTML content is available, render it with sanitization
  if (htmlContent) {
    // Process to convert plain text wikilinks/hashtags before sanitizing
    const processedHtml = processHtmlContent(htmlContent);
    const sanitizedHtml = DOMPurify.sanitize(processedHtml, sanitizeConfig);

    return (
      <div
        className={`note-content-renderer note-content-html ${className}`}
        dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
        onClick={handleContentClick}
      />
    );
  }

  // Fallback to markdown rendering
  if (content) {
    // Handle checkbox click by extracting text from parent list item
    const handleCheckboxChange = (e) => {
      e.stopPropagation();
      if (!onCheckboxToggle) return;

      // Find parent li element and get its text content
      const checkbox = e.target;
      const listItem = checkbox.closest('li');
      if (listItem) {
        // Get the text content after the checkbox (exclude the checkbox itself)
        const textContent = listItem.textContent?.trim() || '';
        if (textContent) {
          onCheckboxToggle(textContent, checkbox.checked);
        }
      }
    };

    return (
      <div className={`note-content-renderer note-content-markdown ${className}`}>
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            // Style checkboxes - make them interactive
            input: ({ node, checked, disabled, type, ...props }) => {
              // Only handle checkbox inputs
              if (type !== 'checkbox') {
                return <input type={type} disabled={disabled} {...props} />;
              }

              // For GFM task lists, 'checked' will be a boolean (true/false)
              const isRealCheckbox = typeof checked === 'boolean';
              const isInteractive = !!onCheckboxToggle && isRealCheckbox;

              return (
                <input
                  type="checkbox"
                  checked={checked || false}
                  disabled={!isInteractive}
                  className={`note-checkbox ${isInteractive ? 'interactive' : ''}`}
                  onChange={handleCheckboxChange}
                  onClick={(e) => e.stopPropagation()}
                />
              );
            },
            // Style wikilinks (if using markdown [[link]] syntax)
            a: ({ node, href, children, ...props }) => {
              if (href && href.startsWith('[[') && href.endsWith(']]')) {
                const title = href.slice(2, -2);
                return (
                  <span
                    className="wikilink"
                    onClick={() => onWikilinkClick && onWikilinkClick(title)}
                    {...props}
                  >
                    {children}
                  </span>
                );
              }
              return <a href={href} {...props}>{children}</a>;
            },
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    );
  }

  // Empty state
  return (
    <div className={`note-content-renderer note-content-empty ${className}`}>
      <p className="empty-text">No content</p>
    </div>
  );
}

export default NoteContentRenderer;
