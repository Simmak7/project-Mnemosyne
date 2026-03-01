/**
 * AIChatLayout - Main 3-pane container for AI Chat
 *
 * Layout: [ConversationPane | ChatCanvas | ContextRadar]
 * Matches Neural Glass design from Gallery and Notes sections.
 *
 * Keyboard Shortcuts:
 * - Ctrl/Cmd + N: New conversation
 * - Ctrl/Cmd + /: Focus chat input
 * - Ctrl/Cmd + K: Focus conversation search
 * - Escape: Close preview panel
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { ChevronRight, MessageSquare, MessageCircle, Settings } from 'lucide-react';
import { AIChatProvider, useAIChatActions } from '../hooks/AIChatContext';
import { useAIChatKeyboardShortcuts } from '../hooks/useAIChatKeyboardShortcuts';
import { useIsMobile } from '../../../hooks/useIsMobile';
import { useSwipeNavigation } from '../../../hooks/useSwipeNavigation';
import MobilePanelTabs from '../../../components/MobilePanelTabs';
import ConversationPane from './ConversationPane';
import ChatCanvas from './ChatCanvas';
import ContextRadar from './ContextRadar';
import './AIChatLayout.css';

const MOBILE_PANELS = [
  { id: 'chats', label: 'Chats', icon: MessageSquare },
  { id: 'chat', label: 'Chat', icon: MessageCircle },
  { id: 'context', label: 'Context', icon: Settings },
];

const PANEL_IDS = MOBILE_PANELS.map(p => p.id);

/**
 * Inner layout component that uses keyboard shortcuts
 * Must be inside AIChatProvider to access actions
 */
function AIChatLayoutInner({ onNavigateToNote, onNavigateToImage, initialContext, onClearContext }) {
  const isMobile = useIsMobile();
  const [mobilePanel, setMobilePanel] = useState('chat');

  // Panel collapse state
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);

  // Initial query from deep linking
  const [pendingQuery, setPendingQuery] = useState(null);

  // Panel refs for programmatic collapse/expand
  const leftPanelRef = useRef(null);
  const rightPanelRef = useRef(null);

  // Refs for keyboard shortcut targets
  const chatCanvasRef = useRef(null);
  const searchInputRef = useRef(null);

  // Get actions from context
  const { clearMessages, clearPreview, setPreview } = useAIChatActions();

  const swipeHandlers = useSwipeNavigation(PANEL_IDS, mobilePanel, setMobilePanel);

  // Handle initial context from deep linking (e.g., "Ask AI about this note")
  useEffect(() => {
    if (initialContext && onClearContext) {
      clearMessages();
      setPreview({ type: initialContext.type, id: initialContext.id });
      const queryPrefix = initialContext.type === 'note'
        ? 'What can you tell me about my note titled'
        : 'What can you tell me about this image';
      const query = `${queryPrefix} "${initialContext.title}"?`;
      setPendingQuery(query);
      onClearContext();
      if (isMobile) {
        setMobilePanel('chat');
      } else if (rightCollapsed && rightPanelRef.current) {
        rightPanelRef.current.expand();
      }
    }
  }, [initialContext, onClearContext, setPreview, rightCollapsed, clearMessages, isMobile]);

  // Collapse/expand handlers
  const handleCollapseLeft = useCallback(() => {
    leftPanelRef.current?.collapse();
  }, []);

  const handleExpandLeft = useCallback(() => {
    leftPanelRef.current?.expand();
  }, []);

  const handleCollapseRight = useCallback(() => {
    rightPanelRef.current?.collapse();
  }, []);

  const handleExpandRight = useCallback(() => {
    rightPanelRef.current?.expand();
  }, []);

  // Keyboard shortcut handlers
  const handleNewChat = useCallback(() => {
    clearMessages();
  }, [clearMessages]);

  const handleFocusInput = useCallback(() => {
    chatCanvasRef.current?.focusInput();
  }, []);

  const handleFocusSearch = useCallback(() => {
    if (isMobile) {
      setMobilePanel('chats');
    } else {
      if (leftCollapsed && leftPanelRef.current) {
        leftPanelRef.current.expand();
      }
      searchInputRef.current?.focus();
    }
  }, [leftCollapsed, isMobile]);

  const handleClearPreview = useCallback(() => {
    clearPreview();
  }, [clearPreview]);

  useAIChatKeyboardShortcuts({
    onNewChat: handleNewChat,
    onFocusInput: handleFocusInput,
    onFocusSearch: handleFocusSearch,
    onClearPreview: handleClearPreview,
    enabled: true,
  });

  // Mobile layout
  if (isMobile) {
    return (
      <div className="ai-chat-layout ng-theme ai-chat-layout--mobile">
        <MobilePanelTabs panels={MOBILE_PANELS} activePanel={mobilePanel} onPanelChange={setMobilePanel} />
        <div className="ai-chat-mobile-content" {...swipeHandlers}>
          {mobilePanel === 'chats' && (
            <ConversationPane isCollapsed={false} onCollapse={() => {}} searchInputRef={searchInputRef} />
          )}
          {mobilePanel === 'chat' && (
            <ChatCanvas
              ref={chatCanvasRef}
              onNavigateToNote={onNavigateToNote}
              onNavigateToImage={onNavigateToImage}
              initialQuery={pendingQuery}
              onClearInitialQuery={() => setPendingQuery(null)}
            />
          )}
          {mobilePanel === 'context' && (
            <ContextRadar
              isCollapsed={false}
              onCollapse={() => {}}
              onNavigateToNote={onNavigateToNote}
              onNavigateToImage={onNavigateToImage}
            />
          )}
        </div>
      </div>
    );
  }

  // Desktop layout (unchanged)
  return (
    <div className="ai-chat-layout ng-theme">
      <PanelGroup direction="horizontal" className="ai-chat-panel-group">
        <Panel
          ref={leftPanelRef}
          defaultSize={leftCollapsed ? 0 : 20}
          minSize={leftCollapsed ? 0 : 15}
          maxSize={30}
          collapsible={true}
          collapsedSize={0}
          onCollapse={() => setLeftCollapsed(true)}
          onExpand={() => setLeftCollapsed(false)}
          className="ai-chat-panel ai-chat-left-panel"
          id="ai-chat-left"
        >
          <ConversationPane
            isCollapsed={leftCollapsed}
            onCollapse={handleCollapseLeft}
            searchInputRef={searchInputRef}
          />
        </Panel>

        {leftCollapsed && (
          <button
            className="ai-chat-expand-floating left"
            onClick={handleExpandLeft}
            title="Show conversations (Ctrl+K)"
          >
            <ChevronRight size={18} />
          </button>
        )}

        <PanelResizeHandle className="ai-chat-resize-handle" />

        <Panel
          defaultSize={50}
          minSize={35}
          className="ai-chat-panel ai-chat-center-panel"
          id="ai-chat-center"
        >
          <ChatCanvas
            ref={chatCanvasRef}
            onNavigateToNote={onNavigateToNote}
            onNavigateToImage={onNavigateToImage}
            initialQuery={pendingQuery}
            onClearInitialQuery={() => setPendingQuery(null)}
          />
        </Panel>

        <PanelResizeHandle className="ai-chat-resize-handle" />

        <Panel
          ref={rightPanelRef}
          defaultSize={rightCollapsed ? 0 : 30}
          minSize={rightCollapsed ? 0 : 20}
          maxSize={40}
          collapsible={true}
          collapsedSize={0}
          onCollapse={() => setRightCollapsed(true)}
          onExpand={() => setRightCollapsed(false)}
          className="ai-chat-panel ai-chat-right-panel"
          id="ai-chat-right"
        >
          <ContextRadar
            isCollapsed={rightCollapsed}
            onCollapse={handleCollapseRight}
            onNavigateToNote={onNavigateToNote}
            onNavigateToImage={onNavigateToImage}
          />
        </Panel>

        {rightCollapsed && (
          <button
            className="ai-chat-expand-floating right"
            onClick={handleExpandRight}
            title="Show context & settings"
          >
            <ChevronRight size={18} style={{ transform: 'rotate(180deg)' }} />
          </button>
        )}
      </PanelGroup>
    </div>
  );
}

/**
 * AIChatLayout - Main 3-column AI chat container
 * Wraps inner layout with AIChatProvider
 */
function AIChatLayout({ onNavigateToNote, onNavigateToImage, initialContext, onClearContext }) {
  return (
    <AIChatProvider>
      <AIChatLayoutInner
        onNavigateToNote={onNavigateToNote}
        onNavigateToImage={onNavigateToImage}
        initialContext={initialContext}
        onClearContext={onClearContext}
      />
    </AIChatProvider>
  );
}

export default AIChatLayout;
