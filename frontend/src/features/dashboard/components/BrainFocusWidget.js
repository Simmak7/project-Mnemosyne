/**
 * BrainFocusWidget - Spotlight card for the Brain's focused node
 */
import React from 'react';
import { FileText, Tag, Image, Zap, Link } from 'lucide-react';
import GlassPanel from '../../../components/layout/GlassPanel';
import { useBrainFocus } from '../hooks/useBrainFocus';
import BrainFocusMiniGraph from './BrainFocusMiniGraph';
import './BrainFocusWidget.css';

const TYPE_ICONS = { note: FileText, tag: Tag, image: Image, entity: Zap };

function getNodeTitle(node, nodeType, nodeId, tags) {
  if (nodeType === 'note') return node?.title || 'Untitled Note';
  if (nodeType === 'image') return node?.display_name || 'Untitled Image';
  if (nodeType === 'tag') {
    const tag = (tags || []).find(t => String(t.id) === String(nodeId));
    return tag ? `#${tag.name}` : `#tag-${nodeId}`;
  }
  return `Entity ${nodeId}`;
}

function getNodeExcerpt(node, nodeType, tags, nodeId) {
  if (nodeType === 'note') {
    const raw = node?.content || '';
    return raw.replace(/[#*_`>\[\]]/g, '').trim().slice(0, 140);
  }
  if (nodeType === 'image') return node?.ai_analysis_result?.description || '';
  if (nodeType === 'tag') {
    const tag = (tags || []).find(t => String(t.id) === String(nodeId));
    return tag ? `${tag.note_count || 0} notes with this tag` : '';
  }
  return '';
}

function getConnectionCount(node, nodeType) {
  if (nodeType === 'note') {
    const backlinks = node?.backlinks?.length || 0;
    const linked = node?.linked_notes?.length || 0;
    const images = node?.image_ids?.length || 0;
    return backlinks + linked + images;
  }
  if (nodeType === 'image') return (node?.tags || []).length;
  return 0;
}

function BrainFocusWidget({ tags, onNavigateToNote, onNavigateToImage, onTabChange }) {
  const { node, isLoading, nodeType, nodeId, focusNodeId } = useBrainFocus();
  const hasFocus = !!focusNodeId;
  const hasData = hasFocus && (node || nodeType === 'tag' || nodeType === 'entity');

  const TypeIcon = TYPE_ICONS[nodeType] || Zap;
  const title = hasData ? getNodeTitle(node, nodeType, nodeId, tags) : '';
  const excerpt = hasData ? getNodeExcerpt(node, nodeType, tags, nodeId) : '';
  const connections = hasData ? getConnectionCount(node, nodeType) : 0;
  const nodeTags = (nodeType === 'note' && node?.tags) || [];

  const handleOpen = () => {
    if (nodeType === 'note') onNavigateToNote?.(Number(nodeId));
    else if (nodeType === 'image') onNavigateToImage?.(Number(nodeId));
    else onTabChange?.('notes');
  };

  return (
    <GlassPanel variant="default" padding="md" className="dashboard-widget">
      <div className="widget-header">
        <div className="widget-title-row">
          <Zap size={16} className="widget-icon" />
          <span className="widget-title">Brain Focus</span>
        </div>
        {hasData && (
          <button className="widget-action" onClick={() => onTabChange?.('graph')}>
            View graph
          </button>
        )}
      </div>
      <div className="widget-body">
        {isLoading ? (
          <div className="widget-skeleton">
            <div className="widget-skeleton-line ng-shimmer" />
            <div className="widget-skeleton-line ng-shimmer" style={{ width: '75%' }} />
          </div>
        ) : hasData ? (
          <div className="brain-focus-card">
            <BrainFocusMiniGraph focusNodeId={focusNodeId} onTabChange={onTabChange} />
            <span className={`brain-focus-type brain-focus-type--${nodeType}`}>
              <TypeIcon size={12} /> {nodeType}
            </span>
            <h3 className="brain-focus-title">{title}</h3>
            {excerpt && <p className="brain-focus-excerpt">{excerpt}</p>}
            <div className="brain-focus-meta">
              {connections > 0 && (
                <span className="brain-focus-connections">
                  <Link size={12} /> {connections} connections
                </span>
              )}
              {nodeTags.slice(0, 3).map(tag => (
                <span key={tag.id || tag.name} className="brain-focus-tag">
                  #{tag.name}
                </span>
              ))}
            </div>
            <div className="brain-focus-actions">
              <button className="brain-focus-btn brain-focus-btn--primary" onClick={handleOpen}>
                Open
              </button>
              <button
                className="brain-focus-btn brain-focus-btn--secondary"
                onClick={() => onTabChange?.('graph')}
              >
                View in Brain
              </button>
            </div>
          </div>
        ) : (
          <div className="brain-focus-empty">
            <Zap size={24} className="widget-icon" />
            <p className="brain-focus-empty-text">
              Explore your Brain graph to set a focus node
            </p>
            <button
              className="brain-focus-btn brain-focus-btn--secondary"
              onClick={() => onTabChange?.('graph')}
            >
              Open Brain Graph
            </button>
          </div>
        )}
      </div>
    </GlassPanel>
  );
}

export default BrainFocusWidget;
