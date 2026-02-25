/**
 * AIActivityWidget - AI conversations, brain indexing, training status
 */
import React from 'react';
import { Sparkles } from 'lucide-react';
import WidgetShell from './WidgetShell';

function AIActivityWidget({ brainStatus, ragConversations, isLoading, onTabChange }) {
  const conversationCount = Array.isArray(ragConversations)
    ? ragConversations.length
    : (ragConversations?.total ?? null);

  const notesIndexed = brainStatus?.notes_indexed;
  const imagesIndexed = brainStatus?.images_indexed;
  const brainReady = brainStatus?.status === 'ready' || brainStatus?.status === 'indexed';
  const statusLabel = brainStatus?.status === 'ready' ? 'Ready'
    : brainStatus?.status === 'indexed' ? 'Indexed'
    : brainStatus?.status === 'training' ? 'Training...'
    : brainStatus?.status === 'indexing' ? 'Indexing...'
    : 'Not indexed';

  return (
    <WidgetShell
      icon={Sparkles}
      title="AI Activity"
      action={() => onTabChange('chat')}
      actionLabel="Open AI Chat"
      isLoading={isLoading}
    >
      <div className="widget-stats-summary">
        {conversationCount != null && (
          <div className="widget-stat">
            <span className="widget-stat-value">{conversationCount}</span>
            <span className="widget-stat-label">Conversations</span>
          </div>
        )}
        {notesIndexed != null && (
          <div className="widget-stat">
            <span className="widget-stat-value">{notesIndexed}</span>
            <span className="widget-stat-label">Notes Indexed</span>
          </div>
        )}
        {imagesIndexed != null && (
          <div className="widget-stat">
            <span className="widget-stat-value">{imagesIndexed}</span>
            <span className="widget-stat-label">Images Indexed</span>
          </div>
        )}
      </div>

      {brainStatus && (
        <div className="widget-status-row" style={{ marginTop: 8 }}>
          <span className={`widget-status-dot ${brainReady ? 'status-ok' : 'status-unknown'}`} />
          <span className="widget-status-label">Brain</span>
          <span className="widget-status-detail">{statusLabel}</span>
        </div>
      )}
    </WidgetShell>
  );
}

export default AIActivityWidget;
