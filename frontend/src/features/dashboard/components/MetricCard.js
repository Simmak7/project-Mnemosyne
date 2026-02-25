/**
 * MetricCard - Reusable stat card with icon, value, label, subtitle
 */
import React from 'react';
import GlassPanel from '../../../components/layout/GlassPanel';

const ACCENT_COLORS = {
  note: '#fbbf24',
  image: '#22d3ee',
  document: '#818cf8',
  tag: '#34d399',
};

function MetricCard({ icon: Icon, value, label, subtitle, accent = 'note', onClick }) {
  const color = ACCENT_COLORS[accent] || ACCENT_COLORS.note;

  return (
    <GlassPanel
      variant="interactive"
      padding="md"
      className="metric-card"
      onClick={onClick}
      style={{ borderLeft: `3px solid ${color}` }}
    >
      <div className="metric-card__header">
        {Icon && <Icon size={18} style={{ color }} />}
      </div>
      <div className="metric-card__value" style={{ color }}>
        {typeof value === 'number' ? value.toLocaleString() : value ?? '--'}
      </div>
      <div className="metric-card__label">{label}</div>
      {subtitle && <div className="metric-card__subtitle">{subtitle}</div>}
    </GlassPanel>
  );
}

export default MetricCard;
