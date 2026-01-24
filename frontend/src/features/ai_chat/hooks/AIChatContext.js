/**
 * AIChatContext - Global persistent state for AI Chat
 *
 * Provides:
 * - Conversation state that survives page navigation
 * - localStorage persistence for cross-session memory
 * - Preview item tracking for ContextRadar
 * - Settings management
 */

import React, { createContext, useContext, useReducer, useEffect, useCallback } from 'react';

const AIChatContext = createContext(null);

const STORAGE_KEY = 'mnemosyne_ai_chat_state';
const SETTINGS_KEY = 'mnemosyne_ai_chat_settings';

// Default settings
const defaultSettings = {
  model: 'llama3.1:8b',
  temperature: 0.7,
  maxSources: 10,
  includeImages: true,
  includeGraph: true,
  minSimilarity: 0.5,
  useStreaming: true,
};

// Initial state
const initialState = {
  // Current conversation
  conversationId: null,
  messages: [],

  // UI state
  isLoading: false,
  isStreaming: false,
  error: null,

  // Preview for ContextRadar
  previewItem: null, // { type: 'note'|'image', id: number }

  // Active citations from the latest response
  activeCitations: [],

  // Last retrieval metadata
  lastRetrievalMetadata: null,
};

// Action types
const ActionTypes = {
  SET_CONVERSATION: 'SET_CONVERSATION',
  ADD_MESSAGE: 'ADD_MESSAGE',
  UPDATE_MESSAGE: 'UPDATE_MESSAGE',
  SET_MESSAGES: 'SET_MESSAGES',
  CLEAR_MESSAGES: 'CLEAR_MESSAGES',
  SET_LOADING: 'SET_LOADING',
  SET_STREAMING: 'SET_STREAMING',
  SET_ERROR: 'SET_ERROR',
  SET_PREVIEW: 'SET_PREVIEW',
  CLEAR_PREVIEW: 'CLEAR_PREVIEW',
  SET_ACTIVE_CITATIONS: 'SET_ACTIVE_CITATIONS',
  SET_RETRIEVAL_METADATA: 'SET_RETRIEVAL_METADATA',
  RESET_STATE: 'RESET_STATE',
};

// Reducer
function chatReducer(state, action) {
  switch (action.type) {
    case ActionTypes.SET_CONVERSATION:
      return { ...state, conversationId: action.payload };

    case ActionTypes.ADD_MESSAGE:
      return { ...state, messages: [...state.messages, action.payload] };

    case ActionTypes.UPDATE_MESSAGE:
      return {
        ...state,
        messages: state.messages.map(msg =>
          msg.id === action.payload.id ? { ...msg, ...action.payload.updates } : msg
        ),
      };

    case ActionTypes.SET_MESSAGES:
      return { ...state, messages: action.payload };

    case ActionTypes.CLEAR_MESSAGES:
      return { ...state, messages: [], conversationId: null, lastRetrievalMetadata: null };

    case ActionTypes.SET_LOADING:
      return { ...state, isLoading: action.payload };

    case ActionTypes.SET_STREAMING:
      return { ...state, isStreaming: action.payload };

    case ActionTypes.SET_ERROR:
      return { ...state, error: action.payload };

    case ActionTypes.SET_PREVIEW:
      return { ...state, previewItem: action.payload };

    case ActionTypes.CLEAR_PREVIEW:
      return { ...state, previewItem: null };

    case ActionTypes.SET_ACTIVE_CITATIONS:
      return { ...state, activeCitations: action.payload };

    case ActionTypes.SET_RETRIEVAL_METADATA:
      return { ...state, lastRetrievalMetadata: action.payload };

    case ActionTypes.RESET_STATE:
      return { ...initialState };

    default:
      return state;
  }
}

// Load state from localStorage
function loadPersistedState() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      // Only restore messages and conversationId, not UI state
      return {
        ...initialState,
        conversationId: parsed.conversationId || null,
        messages: parsed.messages || [],
      };
    }
  } catch (error) {
    console.warn('Failed to load AI chat state:', error);
  }
  return initialState;
}

// Load settings from localStorage
function loadSettings() {
  try {
    const stored = localStorage.getItem(SETTINGS_KEY);
    if (stored) {
      return { ...defaultSettings, ...JSON.parse(stored) };
    }
  } catch (error) {
    console.warn('Failed to load AI chat settings:', error);
  }
  return defaultSettings;
}

/**
 * Provider component
 */
export function AIChatProvider({ children }) {
  const [state, dispatch] = useReducer(chatReducer, null, loadPersistedState);
  const [settings, setSettingsState] = React.useState(loadSettings);

  // Persist state to localStorage (debounced)
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      try {
        const toStore = {
          conversationId: state.conversationId,
          messages: state.messages,
        };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(toStore));
      } catch (error) {
        console.warn('Failed to save AI chat state:', error);
      }
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [state.conversationId, state.messages]);

  // Persist settings
  useEffect(() => {
    try {
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
    } catch (error) {
      console.warn('Failed to save AI chat settings:', error);
    }
  }, [settings]);

  // Settings updater
  const updateSettings = useCallback((updates) => {
    setSettingsState(prev => ({ ...prev, ...updates }));
  }, []);

  const value = {
    state,
    dispatch,
    settings,
    updateSettings,
    ActionTypes,
  };

  return (
    <AIChatContext.Provider value={value}>
      {children}
    </AIChatContext.Provider>
  );
}

/**
 * Hook to access AI chat context
 */
export function useAIChatContext() {
  const context = useContext(AIChatContext);
  if (!context) {
    throw new Error('useAIChatContext must be used within AIChatProvider');
  }
  return context;
}

/**
 * Hook for common actions (memoized to prevent infinite re-renders)
 */
export function useAIChatActions() {
  const { dispatch, ActionTypes } = useAIChatContext();

  // Memoize all action functions to maintain stable references
  const setConversation = useCallback((id) =>
    dispatch({ type: ActionTypes.SET_CONVERSATION, payload: id }), [dispatch, ActionTypes]);
  const addMessage = useCallback((message) =>
    dispatch({ type: ActionTypes.ADD_MESSAGE, payload: message }), [dispatch, ActionTypes]);
  const updateMessage = useCallback((id, updates) =>
    dispatch({ type: ActionTypes.UPDATE_MESSAGE, payload: { id, updates } }), [dispatch, ActionTypes]);
  const setMessages = useCallback((messages) =>
    dispatch({ type: ActionTypes.SET_MESSAGES, payload: messages }), [dispatch, ActionTypes]);
  const clearMessages = useCallback(() =>
    dispatch({ type: ActionTypes.CLEAR_MESSAGES }), [dispatch, ActionTypes]);
  const setLoading = useCallback((loading) =>
    dispatch({ type: ActionTypes.SET_LOADING, payload: loading }), [dispatch, ActionTypes]);
  const setStreaming = useCallback((streaming) =>
    dispatch({ type: ActionTypes.SET_STREAMING, payload: streaming }), [dispatch, ActionTypes]);
  const setError = useCallback((error) =>
    dispatch({ type: ActionTypes.SET_ERROR, payload: error }), [dispatch, ActionTypes]);
  const setPreview = useCallback((item) =>
    dispatch({ type: ActionTypes.SET_PREVIEW, payload: item }), [dispatch, ActionTypes]);
  const clearPreview = useCallback(() =>
    dispatch({ type: ActionTypes.CLEAR_PREVIEW }), [dispatch, ActionTypes]);
  const setActiveCitations = useCallback((citations) =>
    dispatch({ type: ActionTypes.SET_ACTIVE_CITATIONS, payload: citations }), [dispatch, ActionTypes]);
  const setRetrievalMetadata = useCallback((metadata) =>
    dispatch({ type: ActionTypes.SET_RETRIEVAL_METADATA, payload: metadata }), [dispatch, ActionTypes]);
  const resetState = useCallback(() =>
    dispatch({ type: ActionTypes.RESET_STATE }), [dispatch, ActionTypes]);

  // Return memoized object with stable function references
  return React.useMemo(() => ({
    setConversation,
    addMessage,
    updateMessage,
    setMessages,
    clearMessages,
    setLoading,
    setStreaming,
    setError,
    setPreview,
    clearPreview,
    setActiveCitations,
    setRetrievalMetadata,
    resetState,
  }), [
    setConversation, addMessage, updateMessage, setMessages, clearMessages,
    setLoading, setStreaming, setError, setPreview, clearPreview,
    setActiveCitations, setRetrievalMetadata, resetState
  ]);
}

export default AIChatContext;
