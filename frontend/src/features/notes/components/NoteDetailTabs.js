import React from 'react';
import { FileText, Network, Info, Sparkles } from 'lucide-react';

/**
 * NoteDetailTabs - Tab navigation for note detail panel
 * Tabs: Content | AI Tools | Context | Info
 */
function NoteDetailTabs({ activeTab, onTabChange, contextCount = 0 }) {
  const tabs = [
    { id: 'content', label: 'Content', icon: FileText },
    { id: 'ai', label: 'AI Tools', icon: Sparkles },
    { id: 'context', label: 'Context', icon: Network, count: contextCount },
    { id: 'info', label: 'Info', icon: Info }
  ];

  return (
    <nav className="note-detail-tabs">
      {tabs.map(tab => {
        const Icon = tab.icon;
        const isActive = activeTab === tab.id;

        return (
          <button
            key={tab.id}
            className={`tab-btn ${isActive ? 'active' : ''}`}
            onClick={() => onTabChange(tab.id)}
          >
            <Icon size={14} />
            <span>{tab.label}</span>
            {tab.count > 0 && (
              <span className="tab-count">{tab.count}</span>
            )}
          </button>
        );
      })}
    </nav>
  );
}

export default NoteDetailTabs;
