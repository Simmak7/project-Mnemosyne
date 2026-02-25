/**
 * Inspector - Right panel showing selected node/edge details
 *
 * Displays metadata, connections, and actions for the selected item.
 * Also shows "Why Connected?" for edges.
 */

import React, { useState } from 'react';
import {
  X, FileText, Tag, Image, Sparkles, ExternalLink,
  Maximize2, Pin, PinOff, Calendar, Route, Target, Link2,
  ChevronDown, ChevronUp, FileScan
} from 'lucide-react';
import { getNodeColor } from '../utils/nodeRendering';
import { formatDate, getNodeId, getNodePath } from '../utils/nodeHelpers';
import { EdgeDetails } from './EdgeDetails';
import { BacklinksSection } from './BacklinksSection';
import { API_URL as API_BASE } from '../../../utils/api';
import './Inspector.css';

// Icon mapping for node types
const NODE_ICONS = {
  note: FileText,
  tag: Tag,
  image: Image,
  media: Image,
  document: FileScan,
  entity: Sparkles,
};

// Edge type display config
const EDGE_TYPE_CONFIG = {
  wikilink: { label: 'Wikilinks', color: '#e5e7eb' },
  tag: { label: 'Tags', color: '#34d399' },
  image: { label: 'Images', color: '#22d3ee' },
  source: { label: 'Sources', color: '#fb7185' },
  semantic: { label: 'Semantic', color: '#818cf8' },
  mentions: { label: 'Mentions', color: '#a78bfa' },
  session: { label: 'Session', color: '#9ca3af' },
};

function ExcerptBlock({ metadata }) {
  const [expanded, setExpanded] = useState(false);
  const hasMore = metadata.full_excerpt && metadata.full_excerpt.length > (metadata.excerpt?.length || 0);
  const text = expanded ? metadata.full_excerpt : metadata.excerpt;

  return (
    <div className="inspector__excerpt-wrapper">
      <p className={`inspector__excerpt ${!expanded ? 'inspector__excerpt--collapsed' : ''}`}>
        {text}
      </p>
      {hasMore && (
        <button
          className="inspector__excerpt-toggle"
          onClick={() => setExpanded(prev => !prev)}
        >
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          {expanded ? 'Show less' : 'Show more'}
        </button>
      )}
    </div>
  );
}

export function Inspector({
  selectedNode,
  selectedEdge,
  onClose,
  onNavigate,
  onExpandNeighbors,
  onPin,
  onFindPath,
  onSetFocus,
  edgeBreakdown,
  isPinned,
}) {
  // Nothing selected
  if (!selectedNode && !selectedEdge) {
    return (
      <div className="inspector brain-graph__right-panel">
        <div className="inspector__empty">
          <p className="inspector__empty-text">
            Click a node or edge to see details
          </p>
        </div>
      </div>
    );
  }

  // Edge selected - show "Why Connected?"
  if (selectedEdge) {
    return (
      <div className="inspector brain-graph__right-panel">
        <EdgeDetails edge={selectedEdge} onClose={onClose} />
      </div>
    );
  }

  // Node selected
  const [type] = selectedNode.id.split('-');
  const Icon = NODE_ICONS[type] || FileText;
  const colors = getNodeColor(selectedNode);

  return (
    <div className="inspector brain-graph__right-panel">
      {/* Header */}
      <div className="inspector__header">
        <div className="inspector__title-row">
          <Icon size={18} style={{ color: colors.base }} />
          <h3 className="inspector__title">
            {selectedNode.title || selectedNode.id}
          </h3>
        </div>
        <button className="inspector__close" onClick={onClose} title="Close">
          <X size={16} />
        </button>
      </div>

      {/* Type Badge */}
      <div
        className="inspector__type-badge"
        style={{ backgroundColor: colors.glow, color: colors.base }}
      >
        {type}
      </div>

      {/* Image Preview (for image nodes) */}
      {type === 'image' && (
        <section className="inspector__section">
          <div className="inspector__image-preview">
            <img
              src={`${API_BASE}/image/${getNodeId(selectedNode)}`}
              alt={selectedNode.title || 'Image preview'}
              className="inspector__image-thumbnail"
              onError={(e) => {
                // Fallback if image fails to load
                e.target.style.display = 'none';
              }}
            />
          </div>
        </section>
      )}

      {/* Document details */}
      {type === 'document' && selectedNode.metadata && (
        <section className="inspector__section">
          <div className="inspector__meta-row">
            <FileScan size={14} />
            <span>{selectedNode.metadata.documentType || 'PDF'}</span>
          </div>
          {selectedNode.metadata.pageCount && (
            <div className="inspector__meta-row">
              <FileText size={14} />
              <span>{selectedNode.metadata.pageCount} pages</span>
            </div>
          )}
          {selectedNode.metadata.summaryNoteId && (
            <div className="inspector__meta-row">
              <Link2 size={14} />
              <span>Summary note #{selectedNode.metadata.summaryNoteId}</span>
            </div>
          )}
        </section>
      )}

      {/* Metadata */}
      <section className="inspector__section">
        <h4 className="inspector__section-title">Details</h4>

        {selectedNode.metadata?.createdAt && (
          <div className="inspector__meta-row">
            <Calendar size={14} />
            <span>Created {formatDate(selectedNode.metadata.createdAt)}</span>
          </div>
        )}

        {selectedNode.metadata?.updatedAt && (
          <div className="inspector__meta-row">
            <Calendar size={14} />
            <span>Modified {formatDate(selectedNode.metadata.updatedAt)}</span>
          </div>
        )}

        {/* Excerpt for notes */}
        {selectedNode.metadata?.excerpt && (
          <ExcerptBlock metadata={selectedNode.metadata} />
        )}

        {/* Description for images */}
        {selectedNode.metadata?.description && (
          <p className="inspector__excerpt">
            {selectedNode.metadata.description}
          </p>
        )}
      </section>

      {/* Connections */}
      <section className="inspector__section">
        <h4 className="inspector__section-title">Connections</h4>

        {/* Total connections */}
        {(selectedNode.connections > 0 || selectedNode.val > 0) && (
          <div className="inspector__connection-row">
            <Link2 size={14} />
            <span>{selectedNode.connections || selectedNode.val} total</span>
          </div>
        )}

        {/* Breakdown by edge type */}
        {edgeBreakdown && Object.entries(edgeBreakdown)
          .sort(([, a], [, b]) => b - a)
          .map(([edgeType, count]) => {
            const cfg = EDGE_TYPE_CONFIG[edgeType] || { label: edgeType, color: '#9ca3af' };
            return (
              <div key={edgeType} className="inspector__connection-row">
                <span className="inspector__edge-dot" style={{ background: cfg.color }} />
                <span>{count} {cfg.label}</span>
              </div>
            );
          })
        }

        {!selectedNode.connections && !selectedNode.val && !edgeBreakdown && (
          <p className="inspector__empty-connections">No connections found</p>
        )}
      </section>

      {/* Backlinks */}
      <BacklinksSection
        nodeId={selectedNode.id}
        onFocusNode={(id) => onSetFocus?.({ id })}
      />

      {/* Actions */}
      <section className="inspector__section">
        <h4 className="inspector__section-title">Actions</h4>
        <div className="inspector__actions">
          <button
            className="inspector__action"
            onClick={() => onSetFocus?.(selectedNode)}
            title="Center view on this node (reload neighborhood)"
          >
            <Target size={14} />
            Focus
          </button>

          <button
            className="inspector__action"
            onClick={onExpandNeighbors}
            title="Show more neighbors (increase depth)"
          >
            <Maximize2 size={14} />
            Expand
          </button>

          <button
            className="inspector__action"
            onClick={() => onNavigate(getNodePath(selectedNode))}
            title="Open in editor"
          >
            <ExternalLink size={14} />
            Open
          </button>

          <button
            className={`inspector__action ${isPinned ? 'is-active' : ''}`}
            onClick={onPin}
            title={isPinned ? 'Unpin node' : 'Pin node'}
          >
            {isPinned ? <PinOff size={14} /> : <Pin size={14} />}
            {isPinned ? 'Unpin' : 'Pin'}
          </button>

          <button
            className="inspector__action"
            onClick={() => onFindPath?.(selectedNode)}
            title="Find path to another node"
          >
            <Route size={14} />
            Path
          </button>
        </div>
      </section>
    </div>
  );
}

export default Inspector;
