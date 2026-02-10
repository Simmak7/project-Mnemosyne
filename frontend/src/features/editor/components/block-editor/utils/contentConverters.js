/**
 * Content conversion utilities for BlockEditor
 */

/**
 * Convert plain text wikilinks [[Title]] to proper span elements
 */
export function convertWikilinks(html) {
  return html.replace(
    /(?<!data-wikilink-title="[^"]*)\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g,
    (match, title, alias) => {
      const displayText = alias || title;
      const aliasAttr = alias ? ` data-wikilink-alias="${alias}"` : '';
      return `<span data-wikilink-title="${title}"${aliasAttr} class="wikilink-chip" contenteditable="false">[[${displayText}]]</span>`;
    }
  );
}

/**
 * Convert plain text hashtags #tag to proper span elements
 */
export function convertHashtags(html) {
  return html.replace(
    /(?<!data-hashtag="|class="|>)#([a-zA-Z][a-zA-Z0-9_-]*)/g,
    (match, tag) => {
      return `<span data-hashtag="${tag}" class="hashtag-chip" contenteditable="false">#${tag}</span>`;
    }
  );
}

/**
 * Convert plain text to HTML (preserves line breaks, paragraphs, and task lists)
 */
export function convertPlainTextToHtml(text) {
  if (!text) return '';

  // If it already looks like HTML, return as-is
  if (text.includes('<p>') || text.includes('<h') || text.includes('<ul>') || text.includes('<br')) {
    return text;
  }

  const lines = text.split('\n');
  const result = [];
  let inTaskList = false;
  let currentParagraph = [];

  const flushParagraph = () => {
    if (currentParagraph.length > 0) {
      const content = currentParagraph.join('<br>');
      result.push(`<p>${content}</p>`);
      currentParagraph = [];
    }
  };

  const flushTaskList = () => {
    if (inTaskList) {
      result.push('</ul>');
      inTaskList = false;
    }
  };

  for (const line of lines) {
    const trimmed = line.trim();

    // Check for task list item: - [x] or - [ ]
    const taskMatch = trimmed.match(/^-\s*\[([ xX])\]\s*(.*)$/);
    if (taskMatch) {
      flushParagraph();
      if (!inTaskList) {
        result.push('<ul data-type="taskList">');
        inTaskList = true;
      }
      const checked = taskMatch[1].toLowerCase() === 'x';
      const taskContent = taskMatch[2];
      result.push(`<li data-type="taskItem" data-checked="${checked}"><label><input type="checkbox" ${checked ? 'checked' : ''}><span></span></label><div><p>${taskContent}</p></div></li>`);
      continue;
    }

    // Check for regular list item: - text
    const listMatch = trimmed.match(/^-\s+(.+)$/);
    if (listMatch && !trimmed.match(/^-\s*\[/)) {
      flushParagraph();
      flushTaskList();
      result.push(`<ul><li><p>${listMatch[1]}</p></li></ul>`);
      continue;
    }

    // Empty line marks paragraph break
    if (trimmed === '') {
      flushTaskList();
      flushParagraph();
      continue;
    }

    // Regular text - accumulate into paragraph
    flushTaskList();
    currentParagraph.push(trimmed);
  }

  flushTaskList();
  flushParagraph();

  return result.join('');
}

/**
 * Process content to recognize wikilinks and hashtags
 */
export function processContentForEditor(content) {
  if (!content) return '';
  let html = convertPlainTextToHtml(content);
  html = convertWikilinks(html);
  html = convertHashtags(html);
  return html;
}

/**
 * Convert HTML to plain text while preserving line breaks
 */
export function htmlToPlainText(html) {
  let processed = html;

  // Convert wikilinks and hashtags back to plain text format
  processed = processed.replace(
    /<span[^>]*data-wikilink-title="([^"]+)"[^>]*>[^<]*<\/span>/g,
    '[[$1]]'
  );
  processed = processed.replace(
    /<span[^>]*data-hashtag="([^"]+)"[^>]*>#[^<]*<\/span>/g,
    '#$1'
  );

  // Handle task lists (checkboxes)
  processed = processed.replace(
    /<li[^>]*data-checked="true"[^>]*>(.*?)<\/li>/gi,
    '- [x] $1\n'
  );
  processed = processed.replace(
    /<li[^>]*data-checked="false"[^>]*>(.*?)<\/li>/gi,
    '- [ ] $1\n'
  );

  // Convert block elements to proper line breaks
  processed = processed.replace(/<\/p>\s*<p[^>]*>/gi, '\n\n');
  processed = processed.replace(/<br\s*\/?>/gi, '\n');
  processed = processed.replace(/<\/h[1-6]>/gi, '\n\n');
  processed = processed.replace(/<h[1-6][^>]*>/gi, '');
  processed = processed.replace(/<\/li>/gi, '\n');
  processed = processed.replace(/<li[^>]*>/gi, '- ');
  processed = processed.replace(/<\/(ul|ol)>/gi, '\n');
  processed = processed.replace(/<(ul|ol)[^>]*>/gi, '');
  processed = processed.replace(/<\/blockquote>/gi, '\n');
  processed = processed.replace(/<blockquote[^>]*>/gi, '> ');
  processed = processed.replace(/<\/div>/gi, '\n');
  processed = processed.replace(/<p[^>]*>/gi, '');
  processed = processed.replace(/<\/p>/gi, '\n');

  // Remove remaining HTML tags
  processed = processed.replace(/<[^>]+>/g, '');

  // Decode HTML entities
  const tempDiv = document.createElement('div');
  tempDiv.innerHTML = processed;
  let text = tempDiv.textContent || tempDiv.innerText || '';

  // Clean up excessive whitespace
  text = text.replace(/\n{3,}/g, '\n\n');
  text = text.trim();

  return text;
}

/**
 * Get initial content for editor from note
 */
export function getInitialContent(note) {
  if (note?.html_content) {
    let html = note.html_content;
    html = convertWikilinks(html);
    html = convertHashtags(html);
    return html;
  }
  return processContentForEditor(note?.content || '');
}

/**
 * Extract wikilinks and hashtags from HTML content
 */
export function extractLinksAndTags(htmlContent) {
  const wikilinkMatches = htmlContent.matchAll(/data-wikilink-title="([^"]+)"/g);
  const wikilinks = [...wikilinkMatches].map(match => match[1]);

  const hashtagMatches = htmlContent.matchAll(/data-hashtag="([^"]+)"/g);
  const tags = [...hashtagMatches].map(match => match[1]);

  return {
    wikilinks: [...new Set(wikilinks)],
    tags: [...new Set(tags)],
  };
}
