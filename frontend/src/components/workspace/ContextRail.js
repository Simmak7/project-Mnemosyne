import React from 'react';
import { useWorkspaceState } from '../../hooks/useWorkspaceState';
import { useContentAnalysis } from '../../hooks/useContentAnalysis';
import { Link2, Network, Search, Info } from 'lucide-react';
import BacklinksPanel from './BacklinksPanel';
// Neural Glass brain graph (replaces old GraphPreviewPanel)
import { BrainGraphPreview } from '../../features/brain-graph';
import UnlinkedMentionsPanel from './UnlinkedMentionsPanel';
import InfoPanel from './InfoPanel';
import './ContextRail.css';

/**
 * ContextRail - Tabbed context information panel
 * Tabs: Backlinks, Graph Preview, Unlinked Mentions, Info
 */
function ContextRail() {
  const { contextRailTab, setContextTab, selectedNoteId, selectNote, editorState } = useWorkspaceState();

  // Get editor content analysis for live wikilink highlighting
  const editorAnalysis = useContentAnalysis(editorState?.editorInstance, editorState?.noteTitle);

  const tabs = [
    { id: 'backlinks', label: 'Backlinks', icon: Link2 },
    { id: 'graph', label: 'Graph', icon: Network },
    { id: 'mentions', label: 'Mentions', icon: Search },
    { id: 'info', label: 'Info', icon: Info },
  ];

  const renderActivePanel = () => {
    switch (contextRailTab) {
      case 'backlinks':
        return <BacklinksPanel />;
      case 'graph':
        return (
          <BrainGraphPreview
            selectedNoteId={selectedNoteId}
            onSelectNote={selectNote}
            editorWikilinks={editorAnalysis?.wikilinks || []}
            isEditMode={editorState?.isEditMode || false}
          />
        );
      case 'mentions':
        return <UnlinkedMentionsPanel />;
      case 'info':
        return <InfoPanel />;
      default:
        return <BacklinksPanel />;
    }
  };

  return (
    <div className="context-rail">
      {/* Tab navigation */}
      <div className="context-rail-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`context-tab ${contextRailTab === tab.id ? 'active' : ''}`}
            onClick={() => setContextTab(tab.id)}
            aria-label={tab.label}
            title={tab.label}
            data-tab={tab.id}
          >
            <tab.icon size={18} />
            <span className="context-tab-label">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Active panel content */}
      <div className="context-rail-content">
        {renderActivePanel()}
      </div>
    </div>
  );
}

export default ContextRail;
