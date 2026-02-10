/**
 * ContextRadar - Right panel with preview and settings
 *
 * Features:
 * - Preview section showing hovered/clicked citations
 * - Settings section for model configuration
 * - Brain section (for Mnemosyne mode)
 */
import React, { useCallback } from 'react';
import { ChevronRight, Settings } from 'lucide-react';
import { useAIChatContext } from '../../hooks/AIChatContext';
import PreviewSection from './PreviewSection';
import SettingsSection from './SettingsSection';
import BrainSection from './BrainSection';
import BrainFilesPanel from './BrainFilesPanel';
import BrainSettingsSection from './BrainSettingsSection';
import BrainTopicsPanel from '../BrainTopicsPanel';
import '../ContextRadar.css';

function ContextRadar({ isCollapsed, onCollapse, onNavigateToNote, onNavigateToImage }) {
  const { state, dispatch, ActionTypes } = useAIChatContext();
  const isBrainMode = state.chatMode === 'mnemosyne';

  const handleClearPreview = useCallback(() => {
    dispatch({ type: ActionTypes.CLEAR_PREVIEW });
  }, [dispatch, ActionTypes]);

  const handleSelectCitation = useCallback((citation) => {
    dispatch({
      type: ActionTypes.SET_PREVIEW,
      payload: {
        type: citation.source_type,
        id: citation.source_id,
        title: citation.title,
        citation,
      },
    });
  }, [dispatch, ActionTypes]);

  return (
    <div className="context-radar">
      {/* Header */}
      <div className="context-radar-header">
        <div className="context-radar-title">
          <Settings size={16} />
          <span>{isBrainMode ? 'Brain & Settings' : 'Context & Settings'}</span>
        </div>
        <button
          className="collapse-btn"
          onClick={onCollapse}
          title="Collapse panel"
        >
          <ChevronRight size={18} />
        </button>
      </div>

      {/* Scrollable content area */}
      <div className="context-radar-content">
        {isBrainMode ? (
          <>
            {/* Brain Topics Panel - Topic Selection UI */}
            <BrainTopicsPanel currentQuery={state.messages?.slice(-1)?.[0]?.content} />
            {/* Brain Files Panel */}
            <BrainFilesPanel />
            {/* Simplified Settings */}
            <BrainSettingsSection />
          </>
        ) : (
          <>
            {/* Preview Section */}
            <PreviewSection
              previewItem={state.previewItem}
              activeCitations={state.activeCitations}
              onNavigateToNote={onNavigateToNote}
              onNavigateToImage={onNavigateToImage}
              onClear={handleClearPreview}
              onSelectCitation={handleSelectCitation}
            />
            {/* Settings Section */}
            <SettingsSection />
            {/* Brain Section - LoRA training (only if experimental feature enabled) */}
            {localStorage.getItem('ENABLE_LORA_TRAINING') === 'true' && <BrainSection />}
          </>
        )}
      </div>
    </div>
  );
}

export default ContextRadar;
