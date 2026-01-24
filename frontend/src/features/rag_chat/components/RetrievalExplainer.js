/**
 * RetrievalExplainer - Show retrieval process details for explainability
 *
 * Displays:
 * - Retrieval methods used
 * - Source type breakdown
 * - Relevance statistics
 * - Query type detection
 * - Confidence assessment
 */

import React, { useState } from 'react';
import {
  Search,
  Link2,
  Type,
  Image,
  FileText,
  ChevronDown,
  ChevronUp,
  Info,
  CheckCircle,
  AlertCircle,
  HelpCircle,
  Zap,
  BarChart3,
} from 'lucide-react';
import './RetrievalExplainer.css';

/**
 * Get icon for retrieval method
 */
const getMethodIcon = (method) => {
  switch (method) {
    case 'semantic':
      return <Search size={14} />;
    case 'chunk_semantic':
      return <Search size={14} />;
    case 'wikilink':
      return <Link2 size={14} />;
    case 'fulltext':
      return <Type size={14} />;
    case 'image_tag':
    case 'image_link':
      return <Image size={14} />;
    default:
      return <Search size={14} />;
  }
};

/**
 * Get friendly name for retrieval method
 */
const getMethodName = (method) => {
  const names = {
    semantic: 'Semantic Search',
    chunk_semantic: 'Chunk Search',
    wikilink: 'Wikilink Graph',
    fulltext: 'Full-text Search',
    image_tag: 'Image Tags',
    image_link: 'Linked Images',
    image_tag_indirect: 'Related Images',
    direct: 'Direct Reference',
  };
  return names[method] || method;
};

/**
 * Get friendly name for source type
 */
const getSourceTypeName = (type) => {
  const names = {
    note: 'Notes',
    chunk: 'Note Sections',
    image: 'Images',
    image_chunk: 'Image Analyses',
  };
  return names[type] || type;
};

/**
 * Get icon for source type
 */
const getSourceTypeIcon = (type) => {
  switch (type) {
    case 'note':
    case 'chunk':
      return <FileText size={14} />;
    case 'image':
    case 'image_chunk':
      return <Image size={14} />;
    default:
      return <FileText size={14} />;
  }
};

/**
 * Get confidence display info
 */
const getConfidenceInfo = (level, score) => {
  switch (level) {
    case 'high':
      return {
        icon: <CheckCircle size={16} />,
        color: 'success',
        label: 'High Confidence',
        description: 'The AI found strong supporting evidence in your notes.',
      };
    case 'medium':
      return {
        icon: <AlertCircle size={16} />,
        color: 'warning',
        label: 'Medium Confidence',
        description: 'The AI found partial evidence. Some claims may need verification.',
      };
    case 'low':
      return {
        icon: <HelpCircle size={16} />,
        color: 'error',
        label: 'Low Confidence',
        description: 'Limited evidence found. The response may be incomplete or uncertain.',
      };
    default:
      return {
        icon: <Info size={16} />,
        color: 'gray',
        label: 'Unknown',
        description: 'Confidence could not be determined.',
      };
  }
};

/**
 * Get query type display info
 */
const getQueryTypeInfo = (type) => {
  const types = {
    factual: {
      label: 'Factual Question',
      description: 'Looking for specific facts or definitions',
    },
    comparison: {
      label: 'Comparison',
      description: 'Comparing multiple concepts or items',
    },
    exploratory: {
      label: 'Exploratory',
      description: 'Open-ended exploration of a topic',
    },
    procedural: {
      label: 'How-To',
      description: 'Step-by-step instructions or procedures',
    },
    meta: {
      label: 'Meta Query',
      description: 'Questions about your notes themselves',
    },
  };
  return types[type] || { label: type, description: '' };
};

/**
 * RetrievalExplainer component
 */
function RetrievalExplainer({
  metadata,
  confidenceScore,
  confidenceLevel,
  isCollapsible = true,
  defaultExpanded = false,
}) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  if (!metadata) {
    return null;
  }

  const confidenceInfo = getConfidenceInfo(confidenceLevel, confidenceScore);
  const queryTypeInfo = getQueryTypeInfo(metadata.query_type);

  const content = (
    <div className="retrieval-explainer-content">
      {/* Confidence Section */}
      <div className={`explainer-section confidence confidence-${confidenceInfo.color}`}>
        <div className="section-header">
          {confidenceInfo.icon}
          <span className="section-title">{confidenceInfo.label}</span>
          <span className="confidence-score">{Math.round((confidenceScore || 0) * 100)}%</span>
        </div>
        <p className="section-description">{confidenceInfo.description}</p>
      </div>

      {/* Query Type */}
      <div className="explainer-section query-type">
        <div className="section-header">
          <Zap size={16} />
          <span className="section-title">Query Type</span>
        </div>
        <div className="query-type-info">
          <span className="query-type-label">{queryTypeInfo.label}</span>
          <span className="query-type-desc">{queryTypeInfo.description}</span>
        </div>
      </div>

      {/* Retrieval Methods */}
      <div className="explainer-section methods">
        <div className="section-header">
          <Search size={16} />
          <span className="section-title">Search Methods Used</span>
        </div>
        <div className="methods-list">
          {metadata.retrieval_methods_used.map((method, idx) => (
            <span key={idx} className="method-tag">
              {getMethodIcon(method)}
              {getMethodName(method)}
            </span>
          ))}
        </div>
      </div>

      {/* Source Breakdown */}
      <div className="explainer-section sources">
        <div className="section-header">
          <BarChart3 size={16} />
          <span className="section-title">Sources Found</span>
          <span className="source-count">{metadata.sources_used} used</span>
        </div>
        <div className="source-breakdown">
          {Object.entries(metadata.source_type_breakdown).map(([type, count]) => (
            <div key={type} className="source-type-row">
              <span className="source-type-label">
                {getSourceTypeIcon(type)}
                {getSourceTypeName(type)}
              </span>
              <div className="source-bar-container">
                <div
                  className="source-bar"
                  style={{
                    width: `${(count / metadata.sources_used) * 100}%`,
                  }}
                />
              </div>
              <span className="source-count">{count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Stats */}
      <div className="explainer-section stats">
        <div className="stats-grid">
          <div className="stat-item">
            <span className="stat-value">
              {Math.round(metadata.avg_relevance_score * 100)}%
            </span>
            <span className="stat-label">Avg. Relevance</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">~{metadata.context_tokens_approx}</span>
            <span className="stat-label">Context Tokens</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{metadata.total_sources_searched}</span>
            <span className="stat-label">Sources Searched</span>
          </div>
        </div>
        {metadata.context_truncated && (
          <p className="truncation-warning">
            <AlertCircle size={14} />
            Context was truncated due to length limits
          </p>
        )}
      </div>
    </div>
  );

  if (!isCollapsible) {
    return <div className="retrieval-explainer">{content}</div>;
  }

  return (
    <div className={`retrieval-explainer collapsible ${isExpanded ? 'expanded' : ''}`}>
      <button
        className="explainer-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
      >
        <Info size={16} />
        <span>How this answer was generated</span>
        {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>
      {isExpanded && content}
    </div>
  );
}

/**
 * Compact version for inline display
 */
export function RetrievalBadges({ metadata, confidenceLevel }) {
  if (!metadata) return null;

  const confidenceInfo = getConfidenceInfo(confidenceLevel);

  return (
    <div className="retrieval-badges">
      <span className={`badge confidence-${confidenceInfo.color}`}>
        {confidenceInfo.icon}
        {confidenceInfo.label}
      </span>
      <span className="badge methods">
        {metadata.retrieval_methods_used.length} methods
      </span>
      <span className="badge sources">
        {metadata.sources_used} sources
      </span>
    </div>
  );
}

export default RetrievalExplainer;
