/**
 * CitationCard - Display a citation source with relevance and explainability
 *
 * Shows:
 * - Source type (note, image, chunk)
 * - Title and content preview
 * - Relevance score
 * - Retrieval method (semantic, wikilink, fulltext)
 * - Relationship chain for graph results
 */

import React, { useState } from 'react';
import {
  FileText,
  Image,
  Link2,
  Search,
  Type,
  Tag,
  ChevronDown,
  ChevronRight,
  ExternalLink,
} from 'lucide-react';
import './CitationCard.css';

/**
 * Get icon for source type
 */
const getSourceIcon = (sourceType) => {
  switch (sourceType) {
    case 'note':
      return <FileText className="citation-icon" />;
    case 'chunk':
      return <FileText className="citation-icon chunk" />;
    case 'image':
      return <Image className="citation-icon" />;
    default:
      return <FileText className="citation-icon" />;
  }
};

/**
 * Get icon and label for retrieval method
 */
const getMethodInfo = (method) => {
  switch (method) {
    case 'semantic':
      return { icon: <Search size={12} />, label: 'Semantic match', color: 'blue' };
    case 'wikilink':
      return { icon: <Link2 size={12} />, label: 'Wikilink connection', color: 'purple' };
    case 'fulltext':
      return { icon: <Type size={12} />, label: 'Keyword match', color: 'green' };
    case 'image_tag':
      return { icon: <Tag size={12} />, label: 'Tag match', color: 'orange' };
    case 'image_link':
      return { icon: <Link2 size={12} />, label: 'Linked image', color: 'cyan' };
    case 'direct':
      return { icon: <ExternalLink size={12} />, label: 'Direct reference', color: 'gray' };
    default:
      return { icon: <Search size={12} />, label: method, color: 'gray' };
  }
};

/**
 * Format relevance score as percentage
 */
const formatRelevance = (score) => {
  return `${Math.round(score * 100)}%`;
};

/**
 * Get relevance color class
 */
const getRelevanceClass = (score) => {
  if (score >= 0.8) return 'high';
  if (score >= 0.5) return 'medium';
  return 'low';
};

/**
 * CitationCard component
 */
function CitationCard({
  citation,
  isUsed = false,
  isExpanded = false,
  onToggleExpand,
  onNavigate,
}) {
  const [showRelationshipChain, setShowRelationshipChain] = useState(false);

  const methodInfo = getMethodInfo(citation.retrieval_method);
  const hasRelationshipChain = citation.relationship_chain && citation.relationship_chain.length > 0;

  const handleClick = () => {
    if (onNavigate) {
      onNavigate(citation.source_type, citation.source_id);
    }
  };

  const handleToggleExpand = (e) => {
    e.stopPropagation();
    if (onToggleExpand) {
      onToggleExpand(citation.index);
    }
  };

  return (
    <div
      className={`citation-card ${isUsed ? 'used' : ''} ${isExpanded ? 'expanded' : ''}`}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && handleClick()}
    >
      {/* Header */}
      <div className="citation-header">
        <div className="citation-index">[{citation.index}]</div>
        <div className="citation-type">
          {getSourceIcon(citation.source_type)}
        </div>
        <div className="citation-title">
          {citation.title || 'Untitled'}
        </div>
        <button
          className="citation-expand-btn"
          onClick={handleToggleExpand}
          aria-label={isExpanded ? 'Collapse' : 'Expand'}
        >
          {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        </button>
      </div>

      {/* Metadata row */}
      <div className="citation-meta">
        <span className={`citation-method method-${methodInfo.color}`}>
          {methodInfo.icon}
          {methodInfo.label}
        </span>
        <span className={`citation-relevance relevance-${getRelevanceClass(citation.relevance_score)}`}>
          {formatRelevance(citation.relevance_score)} relevant
        </span>
        {citation.hop_count > 0 && (
          <span className="citation-hops">
            {citation.hop_count} hop{citation.hop_count > 1 ? 's' : ''} away
          </span>
        )}
      </div>

      {/* Expanded content */}
      {isExpanded && (
        <div className="citation-expanded">
          {/* Content preview */}
          <div className="citation-preview">
            {citation.content_preview || 'No preview available'}
          </div>

          {/* Relationship chain (for graph results) */}
          {hasRelationshipChain && (
            <div className="citation-relationship">
              <button
                className="relationship-toggle"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowRelationshipChain(!showRelationshipChain);
                }}
              >
                <Link2 size={14} />
                <span>Show connection path</span>
                {showRelationshipChain ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              </button>

              {showRelationshipChain && (
                <div className="relationship-chain">
                  {citation.relationship_chain.map((link, idx) => (
                    <div key={idx} className="relationship-link">
                      <span className="link-from">{link.from_title}</span>
                      <span className="link-arrow">
                        {link.type === 'wikilink' ? '→' : '←'}
                      </span>
                      <span className="link-to">{link.to_title}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Action button */}
          <button
            className="citation-navigate-btn"
            onClick={(e) => {
              e.stopPropagation();
              handleClick();
            }}
          >
            <ExternalLink size={14} />
            Open {citation.source_type}
          </button>
        </div>
      )}
    </div>
  );
}

/**
 * CitationList - Display list of citations with grouping
 */
export function CitationList({
  citations = [],
  usedIndices = [],
  onNavigate,
  showUnused = true,
}) {
  const [expandedIndices, setExpandedIndices] = useState(new Set());

  const toggleExpand = (index) => {
    setExpandedIndices(prev => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  const usedCitations = citations.filter(c => usedIndices.includes(c.index));
  const unusedCitations = citations.filter(c => !usedIndices.includes(c.index));

  if (citations.length === 0) {
    return (
      <div className="citation-list empty">
        <p>No sources found</p>
      </div>
    );
  }

  return (
    <div className="citation-list">
      {/* Used citations */}
      {usedCitations.length > 0 && (
        <div className="citation-group">
          <h4 className="citation-group-title">
            <span className="used-badge">Used</span>
            Sources cited in response ({usedCitations.length})
          </h4>
          {usedCitations.map(citation => (
            <CitationCard
              key={citation.index}
              citation={citation}
              isUsed={true}
              isExpanded={expandedIndices.has(citation.index)}
              onToggleExpand={toggleExpand}
              onNavigate={onNavigate}
            />
          ))}
        </div>
      )}

      {/* Unused citations */}
      {showUnused && unusedCitations.length > 0 && (
        <div className="citation-group unused">
          <h4 className="citation-group-title">
            Additional context ({unusedCitations.length})
          </h4>
          {unusedCitations.map(citation => (
            <CitationCard
              key={citation.index}
              citation={citation}
              isUsed={false}
              isExpanded={expandedIndices.has(citation.index)}
              onToggleExpand={toggleExpand}
              onNavigate={onNavigate}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default CitationCard;
