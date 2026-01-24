/**
 * Inspector - Right panel showing selected node/edge details
 *
 * Displays metadata, connections, and actions for the selected item.
 * Also shows "Why Connected?" for edges.
 */

import React from 'react';
import {
  X, FileText, Tag, Image, Sparkles, ExternalLink,
  Maximize2, Pin, PinOff, ArrowRight, ArrowLeft, Calendar,
  Route, Target, Link2
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { getNodeColor } from '../utils/nodeRendering';
import { getEdgeLabel, getEdgeColor } from '../utils/edgeRendering';
import './Inspector.css';

// Icon mapping for node types
const NODE_ICONS = {
  note: FileText,
  tag: Tag,
  image: Image,
  media: Image,
  entity: Sparkles,
};

// API base for image thumbnails
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export function Inspector({
  selectedNode,
  selectedEdge,
  onClose,
  onNavigate,
  onExpandNeighbors,
  onPin,
  onFindPath,
  onSetFocus,
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
          <p className="inspector__excerpt">
            {selectedNode.metadata.excerpt}
          </p>
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

        {/* Total connections (from val or connections property) */}
        {(selectedNode.connections > 0 || selectedNode.val > 0) && (
          <div className="inspector__connection-row">
            <Link2 size={14} />
            <span>{selectedNode.connections || selectedNode.val} total connections</span>
          </div>
        )}

        {/* Outgoing links if available */}
        {selectedNode.outLinks > 0 && (
          <div className="inspector__connection-row">
            <ArrowRight size={14} />
            <span>{selectedNode.outLinks} outgoing links</span>
          </div>
        )}

        {/* Incoming links if available */}
        {selectedNode.inLinks > 0 && (
          <div className="inspector__connection-row">
            <ArrowLeft size={14} />
            <span>{selectedNode.inLinks} backlinks</span>
          </div>
        )}

        {/* Tags count if available */}
        {selectedNode.tags?.length > 0 && (
          <div className="inspector__connection-row">
            <Tag size={14} />
            <span>{selectedNode.tags.length} tags</span>
          </div>
        )}

        {/* Show message if no connection data */}
        {!selectedNode.connections && !selectedNode.val && !selectedNode.outLinks && !selectedNode.inLinks && (
          <p className="inspector__empty-connections">
            Select node to see connections
          </p>
        )}
      </section>

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

// Edge details sub-component
function EdgeDetails({ edge, onClose }) {
  const colors = getEdgeColor(edge);

  return (
    <>
      <div className="inspector__header">
        <h3 className="inspector__title">Connection</h3>
        <button className="inspector__close" onClick={onClose}>
          <X size={16} />
        </button>
      </div>

      <div
        className="inspector__type-badge"
        style={{ backgroundColor: colors.glow, color: colors.highlight }}
      >
        {edge.type}
      </div>

      <section className="inspector__section">
        <h4 className="inspector__section-title">Why Connected?</h4>
        <p className="inspector__excerpt">
          {getEdgeLabel(edge)}
        </p>
        {edge.weight && (
          <div className="inspector__meta-row">
            <span>Strength: {Math.round(edge.weight * 100)}%</span>
          </div>
        )}
      </section>

      {edge.evidence?.snippets?.length > 0 && (
        <section className="inspector__section">
          <h4 className="inspector__section-title">Evidence</h4>
          {edge.evidence.snippets.map((snippet, i) => (
            <p key={i} className="inspector__snippet">{snippet}</p>
          ))}
        </section>
      )}
    </>
  );
}

// Helper functions
function formatDate(dateStr) {
  try {
    return formatDistanceToNow(new Date(dateStr), { addSuffix: true });
  } catch {
    return dateStr;
  }
}

function getNodeId(node) {
  // Extract numeric ID from node ID (e.g., "image-123" -> "123")
  if (!node?.id) return '';
  const [, ...idParts] = node.id.split('-');
  return idParts.join('-');
}

function getNodePath(node) {
  // Node IDs use format "type-id" (e.g., "note-123", "image-456")
  const [type, ...idParts] = node.id.split('-');
  const id = idParts.join('-'); // Rejoin in case ID contains hyphens
  switch (type) {
    case 'note': return `/notes/${id}`;
    case 'image': return `/gallery?image=${id}`;
    case 'tag': return `/tags/${encodeURIComponent(id)}`;
    default: return '/';
  }
}

export default Inspector;
