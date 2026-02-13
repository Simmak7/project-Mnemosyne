/**
 * NexusInsightsSection - Displays connection insights and exploration suggestions
 *
 * Shows:
 * - Connection insights between sources (shared communities, wikilinks, shared tags)
 * - Exploration suggestions for follow-up queries
 */
import React, { useState } from 'react';
import { Link2, Compass, ArrowRight, ChevronRight } from 'lucide-react';
import { useAIChatContext, useAIChatActions } from '../../hooks/AIChatContext';

function NexusInsightsSection() {
  const { state } = useAIChatContext();
  const { connectionInsights = [], explorationSuggestions = [] } = state;
  const [connectionsOpen, setConnectionsOpen] = useState(false);

  if (!connectionInsights.length && !explorationSuggestions.length) {
    return null;
  }

  return (
    <div className="nexus-insights-section">
      {/* Connection Insights - collapsible */}
      {connectionInsights.length > 0 && (
        <>
          <button
            className="nexus-insights-toggle"
            onClick={() => setConnectionsOpen(o => !o)}
          >
            <ChevronRight size={12} className={`toggle-chevron${connectionsOpen ? ' open' : ''}`} />
            <Link2 size={12} />
            <span>Connections Found</span>
            <span className="nexus-insights-count">{connectionInsights.length}</span>
          </button>
          {connectionsOpen && (
            <div className="nexus-connections-list">
              {connectionInsights.map((insight, i) => (
                <div key={i} className="nexus-connection-item">
                  <span className="nexus-connection-type">
                    {insight.connection_type === 'shared_community' ? 'community' :
                     insight.connection_type === 'wikilink' ? 'link' : 'tag'}
                  </span>
                  <span>{insight.description}</span>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Exploration Suggestions */}
      {explorationSuggestions.length > 0 && (
        <>
          <div className="nexus-insights-title" style={{ marginTop: connectionInsights.length ? 12 : 0 }}>
            <Compass size={12} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
            Explore Next
          </div>
          {explorationSuggestions.map((suggestion, i) => (
            <ExplorationCard key={i} suggestion={suggestion} />
          ))}
        </>
      )}
    </div>
  );
}

function ExplorationCard({ suggestion }) {
  const actions = useAIChatActions();

  const handleClick = () => {
    // Pre-fill the chat with the suggestion query
    // The user can then send it or modify it
    const input = document.querySelector('.chat-input textarea, .chat-input input');
    if (input) {
      const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
        window.HTMLTextAreaElement.prototype, 'value'
      )?.set || Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, 'value'
      )?.set;
      if (nativeInputValueSetter) {
        nativeInputValueSetter.call(input, suggestion.query);
        input.dispatchEvent(new Event('input', { bubbles: true }));
      }
      input.focus();
    }
  };

  return (
    <div className="nexus-suggestion-item" onClick={handleClick}>
      <div style={{ flex: 1 }}>
        <div className="nexus-suggestion-query">{suggestion.query}</div>
        <div className="nexus-suggestion-reason">{suggestion.reason}</div>
      </div>
      <ArrowRight size={14} style={{ opacity: 0.4 }} />
    </div>
  );
}

export default NexusInsightsSection;
