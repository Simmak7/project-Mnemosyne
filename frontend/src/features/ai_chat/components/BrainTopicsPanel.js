/**
 * BrainTopicsPanel - Topic selection UI for Brain mode
 *
 * Shows all brain topics with:
 * - Pinned topics (always loaded)
 * - Auto-selected topics (based on query relevance)
 * - Available topics (can be pinned)
 * - Token budget visualization
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Pin,
  PinOff,
  Brain,
  Loader2,
  ChevronDown,
  ChevronUp,
  Sparkles,
  FileText,
} from 'lucide-react';
import { api } from '../../../utils/api';
import './BrainTopicsPanel.css';

function TopicItem({ topic, onPin, onUnpin }) {
  const isPinned = topic.is_pinned;
  const isAutoSelected = topic.is_auto_selected && !isPinned;

  return (
    <div className={`topic-item ${isPinned ? 'pinned' : ''} ${isAutoSelected ? 'auto-selected' : ''}`}>
      <div className="topic-info">
        <FileText size={12} className="topic-icon" />
        <span className="topic-title">{topic.title}</span>
      </div>
      <div className="topic-meta">
        {topic.score > 0 && (
          <span className="topic-score">{Math.round(topic.score * 100)}%</span>
        )}
        <span className="topic-tokens">{topic.token_count} tok</span>
        {isPinned ? (
          <button
            className="topic-action unpin"
            onClick={() => onUnpin(topic.file_key)}
            title="Unpin topic"
          >
            <PinOff size={12} />
          </button>
        ) : (
          <button
            className="topic-action pin"
            onClick={() => onPin(topic.file_key)}
            title="Pin topic"
          >
            <Pin size={12} />
          </button>
        )}
      </div>
    </div>
  );
}

function TokenBudgetBar({ used, budget }) {
  const percentage = Math.min((used / budget) * 100, 100);
  const isNearLimit = percentage > 80;

  return (
    <div className="token-budget">
      <div className="budget-label">
        Token usage: {used.toLocaleString()} / {budget.toLocaleString()}
      </div>
      <div className="budget-bar">
        <div
          className={`budget-fill ${isNearLimit ? 'near-limit' : ''}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

function BrainTopicsPanel({ currentQuery }) {
  const [topics, setTopics] = useState([]);
  const [pinned, setPinned] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(true);
  const [tokenBudget, setTokenBudget] = useState(3000);
  const [coreTokens, setCoreTokens] = useState(2500);

  // Fetch topics when query changes
  const fetchTopics = useCallback(async (query) => {
    setLoading(true);
    try {
      const url = query
        ? `/mnemosyne/topics/scores?query=${encodeURIComponent(query)}`
        : '/mnemosyne/topics/scores';
      const data = await api.get(url);
      setTopics(data.topics || []);
      setPinned(data.pinned || []);
      setTokenBudget(data.token_budget || 3000);
      setCoreTokens(data.core_tokens_used || 2500);
    } catch (err) {
      console.error('Failed to fetch topics:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch on mount and when query changes
  useEffect(() => {
    fetchTopics(currentQuery);
  }, [currentQuery, fetchTopics]);

  // Handle pinning
  const handlePin = async (topicKey) => {
    try {
      const data = await api.post('/mnemosyne/topics/pin', {
        topic_key: topicKey,
        pin: true,
      });
      setPinned(data.pinned || []);
      // Update topics list to reflect pinned state
      setTopics(prev => prev.map(t =>
        t.file_key === topicKey ? { ...t, is_pinned: true } : t
      ));
    } catch (err) {
      console.error('Failed to pin topic:', err);
    }
  };

  // Handle unpinning
  const handleUnpin = async (topicKey) => {
    try {
      const data = await api.post('/mnemosyne/topics/pin', {
        topic_key: topicKey,
        pin: false,
      });
      setPinned(data.pinned || []);
      // Update topics list to reflect pinned state
      setTopics(prev => prev.map(t =>
        t.file_key === topicKey ? { ...t, is_pinned: false } : t
      ));
    } catch (err) {
      console.error('Failed to unpin topic:', err);
    }
  };

  // Calculate token usage
  const calculateTokenUsage = () => {
    const pinnedTokens = topics
      .filter(t => t.is_pinned)
      .reduce((sum, t) => sum + t.token_count, 0);
    const autoSelectedTokens = topics
      .filter(t => t.is_auto_selected && !t.is_pinned)
      .reduce((sum, t) => sum + t.token_count, 0);
    return pinnedTokens + autoSelectedTokens;
  };

  // Separate topics by category
  const pinnedTopics = topics.filter(t => t.is_pinned);
  const autoSelectedTopics = topics.filter(t => t.is_auto_selected && !t.is_pinned);
  const availableTopics = topics.filter(t => !t.is_auto_selected && !t.is_pinned);

  const tokensUsed = calculateTokenUsage();

  return (
    <div className="brain-topics-panel">
      <button
        className="section-header"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="section-title">
          <Brain size={14} />
          <span>Topics</span>
          {loading && <Loader2 size={12} className="spinning" />}
        </div>
        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {isExpanded && (
        <div className="topics-content">
          {/* Pinned Topics */}
          {pinnedTopics.length > 0 && (
            <div className="topics-section">
              <div className="section-label">
                <Pin size={10} />
                <span>Pinned ({pinnedTopics.length})</span>
              </div>
              {pinnedTopics.map(topic => (
                <TopicItem
                  key={topic.file_key}
                  topic={topic}
                  onPin={handlePin}
                  onUnpin={handleUnpin}
                />
              ))}
            </div>
          )}

          {/* Auto-Selected Topics */}
          {autoSelectedTopics.length > 0 && (
            <div className="topics-section">
              <div className="section-label">
                <Sparkles size={10} />
                <span>Auto-selected ({autoSelectedTopics.length})</span>
              </div>
              {autoSelectedTopics.map(topic => (
                <TopicItem
                  key={topic.file_key}
                  topic={topic}
                  onPin={handlePin}
                  onUnpin={handleUnpin}
                />
              ))}
            </div>
          )}

          {/* Available Topics */}
          {availableTopics.length > 0 && (
            <div className="topics-section">
              <div className="section-label">
                <FileText size={10} />
                <span>Available ({availableTopics.length})</span>
              </div>
              {availableTopics.slice(0, 5).map(topic => (
                <TopicItem
                  key={topic.file_key}
                  topic={topic}
                  onPin={handlePin}
                  onUnpin={handleUnpin}
                />
              ))}
              {availableTopics.length > 5 && (
                <div className="topics-more">
                  +{availableTopics.length - 5} more topics
                </div>
              )}
            </div>
          )}

          {/* No topics message */}
          {topics.length === 0 && !loading && (
            <div className="topics-empty">
              No topics found. Build your brain first.
            </div>
          )}

          {/* Token Budget */}
          <TokenBudgetBar used={tokensUsed} budget={tokenBudget} />
        </div>
      )}
    </div>
  );
}

export default BrainTopicsPanel;
