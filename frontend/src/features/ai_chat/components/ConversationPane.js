/**
 * ConversationPane - Left panel with conversation history
 *
 * Features:
 * - New chat button
 * - Conversation list grouped by date
 * - Brain status card (placeholder for Phase 5)
 * - Collapse functionality
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Plus,
  MessageSquare,
  Brain,
  ChevronLeft,
  Trash2,
  MoreHorizontal,
  Search,
  Pencil,
  Check,
  X,
  Loader2,
  Database,
  Sparkles,
} from 'lucide-react';
import { useAIChat } from '../hooks/useAIChat';
import { useAIChatContext, useAIChatActions } from '../hooks/AIChatContext';
import { useBrain } from '../hooks/useBrain';
import { useMnemosyneBrain } from '../hooks/useMnemosyneBrain';
import './ConversationPane.css';

// Module-level tracking to prevent multiple fetches across component remounts
// This persists even when component is unmounted/remounted (e.g., StrictMode, tab switching)
let globalFetchInProgress = false;
let globalLastFetchTime = 0;
const FETCH_COOLDOWN_MS = 5000; // Minimum 5 seconds between fetches

/**
 * Group conversations by relative date
 */
function groupConversationsByDate(conversations) {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const lastWeek = new Date(today);
  lastWeek.setDate(lastWeek.getDate() - 7);

  const groups = {
    today: [],
    yesterday: [],
    lastWeek: [],
    older: [],
  };

  conversations.forEach(conv => {
    const convDate = new Date(conv.updated_at || conv.created_at);
    const convDay = new Date(convDate.getFullYear(), convDate.getMonth(), convDate.getDate());

    if (convDay >= today) {
      groups.today.push(conv);
    } else if (convDay >= yesterday) {
      groups.yesterday.push(conv);
    } else if (convDay >= lastWeek) {
      groups.lastWeek.push(conv);
    } else {
      groups.older.push(conv);
    }
  });

  return groups;
}

function ConversationPane({ isCollapsed, onCollapse, searchInputRef }) {
  const [conversations, setConversations] = useState([]);
  const [isLoadingList, setIsLoadingList] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeMenu, setActiveMenu] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const editInputRef = useRef(null);
  const internalSearchRef = useRef(null);
  const prevConversationIdRef = useRef(null);
  const hasFetchedRef = useRef(false);

  // Use external ref if provided, otherwise use internal ref
  const actualSearchRef = searchInputRef || internalSearchRef;

  const { loadConversation, deleteConversation, updateConversation, listConversations } = useAIChat();
  const { state, dispatch, ActionTypes } = useAIChatContext();
  const { setChatMode } = useAIChatActions();
  const isBrainMode = state.chatMode === 'mnemosyne';

  // Fetch conversations function with aggressive rate limiting protection
  const fetchConversations = useCallback(async (force = false) => {
    const now = Date.now();

    // Guard 1: Check module-level fetch in progress
    if (globalFetchInProgress) {
      console.log('ConversationPane: Fetch already in progress, skipping');
      return;
    }

    // Guard 2: Check cooldown (unless force refresh)
    if (!force && (now - globalLastFetchTime) < FETCH_COOLDOWN_MS) {
      console.log('ConversationPane: Within cooldown period, skipping');
      return;
    }

    // Guard 3: Component-level ref check
    if (!force && hasFetchedRef.current) {
      console.log('ConversationPane: Already fetched this mount, skipping');
      return;
    }

    // Set all guards before async operation
    globalFetchInProgress = true;
    globalLastFetchTime = now;
    hasFetchedRef.current = true;
    setIsLoadingList(true);

    try {
      const data = await listConversations(0, 100);
      setConversations(data || []);
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
    } finally {
      setIsLoadingList(false);
      globalFetchInProgress = false;
    }
  }, [listConversations]);

  // Fetch conversations on mount only
  useEffect(() => {
    if (!hasFetchedRef.current) {
      fetchConversations();
    }
  }, []);

  // Re-fetch conversations when chat mode changes
  useEffect(() => {
    hasFetchedRef.current = false;
    fetchConversations(true);
  }, [state.chatMode]);

  // Refresh list when a new conversation is auto-created
  useEffect(() => {
    if (state.conversationId && state.conversationId !== prevConversationIdRef.current) {
      // Check if this is a new conversation not in our list
      const exists = conversations.some(c => c.id === state.conversationId);
      if (!exists) {
        // New conversation was created, refresh the list (force=true)
        fetchConversations(true);
      }
      prevConversationIdRef.current = state.conversationId;
    }
  }, [state.conversationId, conversations, fetchConversations]);

  // Focus edit input when editing
  useEffect(() => {
    if (editingId && editInputRef.current) {
      editInputRef.current.focus();
      editInputRef.current.select();
    }
  }, [editingId]);

  // Filter conversations by search
  const filteredConversations = conversations.filter(conv =>
    !searchQuery || (conv.title && conv.title.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  // Group by date
  const groupedConversations = groupConversationsByDate(filteredConversations);

  // Handle new chat
  const handleNewChat = useCallback(async () => {
    try {
      dispatch({ type: ActionTypes.CLEAR_MESSAGES });
      // Don't create a conversation until first message
    } catch (error) {
      console.error('Failed to start new chat:', error);
    }
  }, [dispatch, ActionTypes]);

  // Handle select conversation
  const handleSelectConversation = useCallback(async (conv) => {
    try {
      await loadConversation(conv.id);
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  }, [loadConversation]);

  // Handle delete conversation
  const handleDeleteConversation = useCallback(async (e, convId) => {
    e.stopPropagation();
    try {
      await deleteConversation(convId);
      setConversations(prev => prev.filter(c => c.id !== convId));
      setActiveMenu(null);
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  }, [deleteConversation]);

  // Handle start editing
  const handleStartEdit = useCallback((e, conv) => {
    e.stopPropagation();
    setEditingId(conv.id);
    setEditTitle(conv.title || '');
    setActiveMenu(null);
  }, []);

  // Handle save edit
  const handleSaveEdit = useCallback(async (e, convId) => {
    e.stopPropagation();
    const newTitle = editTitle.trim();
    if (!newTitle) {
      setEditingId(null);
      return;
    }

    try {
      await updateConversation(convId, { title: newTitle });
      setConversations(prev =>
        prev.map(c => c.id === convId ? { ...c, title: newTitle } : c)
      );
      setEditingId(null);
    } catch (error) {
      console.error('Failed to rename conversation:', error);
    }
  }, [editTitle, updateConversation]);

  // Handle cancel edit
  const handleCancelEdit = useCallback((e) => {
    e.stopPropagation();
    setEditingId(null);
    setEditTitle('');
  }, []);

  // Handle edit key press
  const handleEditKeyDown = useCallback((e, convId) => {
    if (e.key === 'Enter') {
      handleSaveEdit(e, convId);
    } else if (e.key === 'Escape') {
      handleCancelEdit(e);
    }
  }, [handleSaveEdit, handleCancelEdit]);

  // Render conversation group
  const renderGroup = (title, items) => {
    if (items.length === 0) return null;

    return (
      <div className="conversation-group" key={title}>
        <div className="conversation-group-header">{title}</div>
        {items.map(conv => (
          <div
            key={conv.id}
            className={`conversation-item ${state.conversationId === conv.id ? 'active' : ''} ${editingId === conv.id ? 'editing' : ''}`}
            onClick={() => editingId !== conv.id && handleSelectConversation(conv)}
          >
            <MessageSquare size={16} className="conversation-icon" />

            {editingId === conv.id ? (
              <div className="conversation-edit-wrapper">
                <input
                  ref={editInputRef}
                  type="text"
                  className="conversation-edit-input"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  onKeyDown={(e) => handleEditKeyDown(e, conv.id)}
                  onClick={(e) => e.stopPropagation()}
                />
                <button
                  className="conversation-edit-btn save"
                  onClick={(e) => handleSaveEdit(e, conv.id)}
                  title="Save"
                >
                  <Check size={14} />
                </button>
                <button
                  className="conversation-edit-btn cancel"
                  onClick={handleCancelEdit}
                  title="Cancel"
                >
                  <X size={14} />
                </button>
              </div>
            ) : (
              <>
                <span className="conversation-title">
                  {conv.title || 'Untitled conversation'}
                </span>
                <button
                  className="conversation-menu-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    setActiveMenu(activeMenu === conv.id ? null : conv.id);
                  }}
                >
                  <MoreHorizontal size={14} />
                </button>

                {activeMenu === conv.id && (
                  <div className="conversation-menu">
                    <button
                      className="conversation-menu-item"
                      onClick={(e) => handleStartEdit(e, conv)}
                    >
                      <Pencil size={14} />
                      Rename
                    </button>
                    <button
                      className="conversation-menu-item delete"
                      onClick={(e) => handleDeleteConversation(e, conv.id)}
                    >
                      <Trash2 size={14} />
                      Delete
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="conversation-pane">
      {/* Header */}
      <div className="conversation-pane-header">
        <div className="conversation-pane-title">
          <Brain size={20} className="brain-icon" />
          <span>Mnemosyne</span>
        </div>
        <button
          className="collapse-btn"
          onClick={onCollapse}
          title="Collapse panel"
        >
          <ChevronLeft size={18} />
        </button>
      </div>

      {/* Mode Toggle */}
      <div className="mode-toggle">
        <button
          className={`mode-toggle-btn ${!isBrainMode ? 'active' : ''}`}
          onClick={() => setChatMode('rag')}
        >
          <Search size={14} />
          <span>RAG</span>
        </button>
        <button
          className={`mode-toggle-btn ${isBrainMode ? 'active' : ''}`}
          onClick={() => setChatMode('mnemosyne')}
        >
          <Brain size={14} />
          <span>Brain</span>
        </button>
      </div>

      {/* New Chat Button */}
      <button className="new-chat-btn" onClick={handleNewChat}>
        <Plus size={18} />
        <span>New Chat</span>
      </button>

      {/* Search */}
      <div className="conversation-search">
        <Search size={14} className="search-icon" />
        <input
          ref={actualSearchRef}
          type="text"
          placeholder="Search conversations... (Ctrl+K)"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {/* Conversation List */}
      <div className="conversation-list">
        {isLoadingList ? (
          <div className="conversation-loading">Loading...</div>
        ) : filteredConversations.length === 0 ? (
          <div className="conversation-empty">
            <MessageSquare size={24} />
            <span>No conversations yet</span>
            <span className="conversation-empty-hint">
              Start a new chat to begin
            </span>
          </div>
        ) : (
          <>
            {renderGroup('Today', groupedConversations.today)}
            {renderGroup('Yesterday', groupedConversations.yesterday)}
            {renderGroup('Last 7 Days', groupedConversations.lastWeek)}
            {renderGroup('Older', groupedConversations.older)}
          </>
        )}
      </div>

      {/* Brain Status Card */}
      {isBrainMode ? <MnemosyneBrainCard /> : <BrainStatusCard />}
    </div>
  );
}

/**
 * Brain Status Card - Shows quick brain status and actions
 */
function BrainStatusCard() {
  const {
    brainStatus,
    hasAdapter,
    activeVersion,
    samplesCount,
    isIndexing,
    isTraining,
    startIndexing,
    startTraining,
    fetchStatus,
    canIndex,
    canTrain,
  } = useBrain();

  // Fetch status on mount
  useEffect(() => {
    fetchStatus();
  }, []);

  // Get status display
  const getStatusDisplay = () => {
    switch (brainStatus) {
      case 'ready':
        return { text: 'Ready', className: 'ready' };
      case 'indexing':
        return { text: 'Indexing...', className: 'indexing' };
      case 'training':
        return { text: 'Training...', className: 'training' };
      case 'indexed':
        return { text: 'Indexed', className: 'indexed' };
      default:
        return { text: 'Not Setup', className: '' };
    }
  };

  const statusDisplay = getStatusDisplay();

  const handleQuickAction = async () => {
    if (samplesCount === 0) {
      // Need to index first
      try {
        await startIndexing(false);
      } catch (err) {
        console.error('Indexing failed:', err);
      }
    } else if (canTrain) {
      // Can train
      try {
        await startTraining();
      } catch (err) {
        console.error('Training failed:', err);
      }
    }
  };

  const isOperating = isIndexing || isTraining;
  const buttonDisabled = isOperating || (hasAdapter && samplesCount === 0);

  return (
    <div className="brain-status-card">
      <div className="brain-status-header">
        <Brain size={16} />
        <span>Brain Status</span>
      </div>
      <div className="brain-status-content">
        <div className="brain-status-row">
          <span className="brain-status-label">Adapter:</span>
          <span className="brain-status-value">
            {hasAdapter ? `v${activeVersion}` : 'Base Model'}
          </span>
        </div>
        <div className="brain-status-row">
          <span className="brain-status-label">Status:</span>
          <span className={`brain-status-value ${statusDisplay.className}`}>
            {isOperating && <Loader2 size={12} className="spinning" />}
            {statusDisplay.text}
          </span>
        </div>
        {samplesCount > 0 && (
          <div className="brain-status-row">
            <span className="brain-status-label">Samples:</span>
            <span className="brain-status-value">{samplesCount}</span>
          </div>
        )}
      </div>
      <button
        className="brain-train-btn"
        onClick={handleQuickAction}
        disabled={buttonDisabled}
      >
        {isIndexing ? (
          <>
            <Loader2 size={14} className="spinning" />
            Indexing...
          </>
        ) : isTraining ? (
          <>
            <Loader2 size={14} className="spinning" />
            Training...
          </>
        ) : samplesCount === 0 ? (
          <>
            <Database size={14} />
            Index Brain
          </>
        ) : (
          <>
            <Sparkles size={14} />
            Train Brain
          </>
        )}
      </button>
    </div>
  );
}

/**
 * MnemosyneBrainCard - Shows Mnemosyne brain status and build actions
 */
function MnemosyneBrainCard() {
  const {
    hasBrain, isReady, isBuilding, isStale,
    fetchBrainStatus, triggerBuild, startBuildPolling,
    buildStatus,
  } = useMnemosyneBrain();

  useEffect(() => {
    fetchBrainStatus();
  }, []);

  const getStatusDisplay = () => {
    if (isBuilding) return { text: 'Building...', className: 'indexing' };
    if (isStale) return { text: 'Stale', className: 'indexed' };
    if (isReady) return { text: 'Ready', className: 'ready' };
    if (hasBrain) return { text: 'Built', className: 'ready' };
    return { text: 'Not Built', className: '' };
  };

  const statusDisplay = getStatusDisplay();

  const handleBuild = async () => {
    try {
      await triggerBuild(true);
    } catch (err) {
      console.error('Brain build failed:', err);
    }
  };

  return (
    <div className="brain-status-card">
      <div className="brain-status-header">
        <Brain size={16} />
        <span>Mnemosyne Brain</span>
      </div>
      <div className="brain-status-content">
        <div className="brain-status-row">
          <span className="brain-status-label">Status:</span>
          <span className={`brain-status-value ${statusDisplay.className}`}>
            {isBuilding && <Loader2 size={12} className="spinning" />}
            {statusDisplay.text}
          </span>
        </div>
        {buildStatus?.progress_pct > 0 && isBuilding && (
          <div className="brain-status-row">
            <span className="brain-status-label">Progress:</span>
            <span className="brain-status-value">{buildStatus.progress_pct}%</span>
          </div>
        )}
      </div>
      <button
        className="brain-train-btn"
        onClick={handleBuild}
        disabled={isBuilding}
      >
        {isBuilding ? (
          <>
            <Loader2 size={14} className="spinning" />
            Building...
          </>
        ) : isStale ? (
          <>
            <Sparkles size={14} />
            Rebuild Brain
          </>
        ) : hasBrain ? (
          <>
            <Sparkles size={14} />
            Rebuild Brain
          </>
        ) : (
          <>
            <Database size={14} />
            Build Brain
          </>
        )}
      </button>
    </div>
  );
}

export default ConversationPane;
