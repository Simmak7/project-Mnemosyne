import React from 'react';
import { FileText, ExternalLink } from 'lucide-react';
import './NoteLink.css';

/**
 * NoteLink - Styled wikilink pill component
 * Renders [[note title]] as an interactive emerald-colored pill
 *
 * @param {Object} props
 * @param {string} props.title - The linked note title
 * @param {string} props.alias - Optional display alias
 * @param {boolean} props.exists - Whether the target note exists
 * @param {Function} props.onClick - Click handler for navigation
 * @param {string} props.className - Additional CSS classes
 */
function NoteLink({
  title,
  alias,
  exists = true,
  onClick,
  className = '',
}) {
  const displayText = alias || title;

  const handleClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (onClick) {
      onClick(title);
    }
  };

  return (
    <span
      className={`ng-note-link ${exists ? '' : 'not-found'} ${className}`}
      onClick={handleClick}
      title={exists ? `Go to: ${title}` : `Create: ${title}`}
      role="link"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          handleClick(e);
        }
      }}
    >
      <FileText size={14} className="ng-note-link-icon" />
      <span className="ng-note-link-text">{displayText}</span>
      {!exists && (
        <ExternalLink size={12} className="ng-note-link-create" />
      )}
    </span>
  );
}

/**
 * NoteLinkInline - Inline version without padding for editor use
 */
export function NoteLinkInline({ title, alias, exists = true, onClick }) {
  const displayText = alias || title;

  const handleClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (onClick) {
      onClick(title);
    }
  };

  return (
    <span
      className={`ng-note-link-inline ${exists ? '' : 'not-found'}`}
      onClick={handleClick}
      title={exists ? `Go to: ${title}` : `Create: ${title}`}
    >
      [[{displayText}]]
    </span>
  );
}

export default NoteLink;
