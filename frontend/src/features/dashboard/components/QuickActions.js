/**
 * QuickActions - Feature shortcut cards
 */
import React from 'react';
import { Upload, Image, FileScan, FileText, BookOpen, Brain, Sparkles } from 'lucide-react';
import GlassPanel from '../../../components/layout/GlassPanel';
import './QuickActions.css';

const ACTIONS = [
  { id: 'upload', icon: Upload, label: 'Studio', color: '#94a3b8' },
  { id: 'gallery', icon: Image, label: 'Gallery', color: '#22d3ee' },
  { id: 'documents', icon: FileScan, label: 'Documents', color: '#818cf8' },
  { id: 'notes', icon: FileText, label: 'Notes', color: '#fbbf24' },
  { id: 'journal', icon: BookOpen, label: 'Journal', color: '#fb923c' },
  { id: 'graph', icon: Brain, label: 'Brain', color: '#f472b6' },
  { id: 'chat', icon: Sparkles, label: 'Mnemos AIs', color: '#a78bfa' },
];

function QuickActions({ onTabChange }) {
  return (
    <div className="quick-actions">
      {ACTIONS.map(({ id, icon: Icon, label, color }) => (
        <GlassPanel
          key={id}
          variant="interactive"
          padding="sm"
          className="quick-action-card"
          onClick={() => onTabChange(id)}
        >
          <Icon size={20} style={{ color }} />
          <span className="quick-action-label">{label}</span>
        </GlassPanel>
      ))}
    </div>
  );
}

export default QuickActions;
