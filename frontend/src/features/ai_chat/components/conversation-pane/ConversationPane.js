/**
 * ConversationPane - Left panel with conversation history
 *
 * Features:
 * - New chat button
 * - Conversation list grouped by date
 * - Brain status card
 * - Collapse functionality
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Plus, Brain, ChevronLeft, Search } from 'lucide-react';
import { useAIChat } from '../../hooks/useAIChat';
import { useAIChatContext, useAIChatActions } from '../../hooks/AIChatContext';
import {
  groupConversationsByDate,
  globalFetchInProgress,
  globalLastFetchTime,
  FETCH_COOLDOWN_MS,
  setGlobalFetchInProgress,
  setGlobalLastFetchTime,
} from './utils/conversationUtils';
import ModeToggle from './components/ModeToggle';
import ConversationList from './components/ConversationList';
import BrainStatusCard from './components/BrainStatusCard';
import MnemosyneBrainCard from './components/MnemosyneBrainCard';
import '../ConversationPane.css';

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

  const actualSearchRef = searchInputRef || internalSearchRef;

  const { loadConversation, deleteConversation, updateConversation, listConversations } = useAIChat();
  const { state, dispatch, ActionTypes } = useAIChatContext();
  const { setChatMode } = useAIChatActions();
  const isBrainMode = state.chatMode === 'mnemosyne';

  // Fetch conversations function with rate limiting protection
  const fetchConversations = useCallback(async (force = false) => {
    const now = Date.now();

    if (globalFetchInProgress) {
      console.log('ConversationPane: Fetch already in progress, skipping');
      return;
    }

    if (!force && (now - globalLastFetchTime) < FETCH_COOLDOWN_MS) {
      console.log('ConversationPane: Within cooldown period, skipping');
      return;
    }

    if (!force && hasFetchedRef.current) {
      console.log('ConversationPane: Already fetched this mount, skipping');
      return;
    }

    setGlobalFetchInProgress(true);
    setGlobalLastFetchTime(now);
    hasFetchedRef.current = true;
    setIsLoadingList(true);

    try {
      const data = await listConversations(0, 100);
      setConversations(data || []);
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
    } finally {
      setIsLoadingList(false);
      setGlobalFetchInProgress(false);
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
      const exists = conversations.some(c => c.id === state.conversationId);
      if (!exists) {
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

  const groupedConversations = groupConversationsByDate(filteredConversations);

  const handleNewChat = useCallback(async () => {
    try {
      dispatch({ type: ActionTypes.CLEAR_MESSAGES });
    } catch (error) {
      console.error('Failed to start new chat:', error);
    }
  }, [dispatch, ActionTypes]);

  const handleSelectConversation = useCallback(async (conv) => {
    try {
      await loadConversation(conv.id);
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  }, [loadConversation]);

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

  const handleStartEdit = useCallback((e, conv) => {
    e.stopPropagation();
    setEditingId(conv.id);
    setEditTitle(conv.title || '');
    setActiveMenu(null);
  }, []);

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

  const handleCancelEdit = useCallback((e) => {
    e.stopPropagation();
    setEditingId(null);
    setEditTitle('');
  }, []);

  const handleEditKeyDown = useCallback((e, convId) => {
    if (e.key === 'Enter') {
      handleSaveEdit(e, convId);
    } else if (e.key === 'Escape') {
      handleCancelEdit(e);
    }
  }, [handleSaveEdit, handleCancelEdit]);

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
      <ModeToggle isBrainMode={isBrainMode} onSetChatMode={setChatMode} />

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
        <ConversationList
          conversations={filteredConversations}
          groupedConversations={groupedConversations}
          currentConversationId={state.conversationId}
          editingId={editingId}
          editTitle={editTitle}
          setEditTitle={setEditTitle}
          activeMenu={activeMenu}
          setActiveMenu={setActiveMenu}
          editInputRef={editInputRef}
          isLoading={isLoadingList}
          onSelect={handleSelectConversation}
          onStartEdit={handleStartEdit}
          onSaveEdit={handleSaveEdit}
          onCancelEdit={handleCancelEdit}
          onEditKeyDown={handleEditKeyDown}
          onDelete={handleDeleteConversation}
        />
      </div>

      {/* Brain Status Card */}
      {isBrainMode ? (
        <MnemosyneBrainCard />
      ) : (
        localStorage.getItem('ENABLE_LORA_TRAINING') === 'true' && <BrainStatusCard />
      )}
    </div>
  );
}

export default ConversationPane;
