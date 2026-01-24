/**
 * LeftPanel - Legend, Layers, and Filters
 *
 * Controls visibility of node/edge types, weight thresholds,
 * and provides a legend for the graph colors.
 */

import React from 'react';
import { FileText, Tag, Image, Sparkles, Link2, Brain, SlidersHorizontal } from 'lucide-react';
import './LeftPanel.css';

// Icon mapping
const ICONS = {
  notes: FileText,
  tags: Tag,
  images: Image,
  entities: Sparkles,
  wikilink: Link2,
  tag: Tag,
  semantic: Brain,
  mentions: Sparkles,
};

export function LeftPanel({ filters, layout, currentView }) {
  const {
    filters: filterState,
    toggleNodeLayer,
    toggleEdgeLayer,
    setMinWeight,
    setDepth,
    NODE_LAYERS,
    EDGE_LAYERS,
  } = filters;

  return (
    <div className="left-panel brain-graph__left-panel">
      {/* Legend */}
      <section className="left-panel__section">
        <h3 className="left-panel__header">Legend</h3>
        <div className="left-panel__legend">
          {Object.entries(NODE_LAYERS).map(([key, config]) => (
            <div key={key} className="left-panel__legend-item">
              <span
                className="left-panel__legend-dot"
                style={{ backgroundColor: config.color }}
              />
              <span className="left-panel__legend-label">{config.label}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Node Layers */}
      <section className="left-panel__section">
        <h3 className="left-panel__header">Layers</h3>
        <div className="left-panel__layers">
          {Object.entries(NODE_LAYERS).map(([key, config]) => {
            const Icon = ICONS[key] || FileText;
            const isActive = filterState.nodeLayers.includes(key);

            return (
              <label key={key} className="left-panel__layer">
                <input
                  type="checkbox"
                  checked={isActive}
                  onChange={() => toggleNodeLayer(key)}
                  className="left-panel__checkbox"
                />
                <Icon
                  size={14}
                  className="left-panel__layer-icon"
                  style={{ color: isActive ? config.color : undefined }}
                />
                <span className="left-panel__layer-label">{config.label}</span>
              </label>
            );
          })}
        </div>
      </section>

      {/* Edge Types */}
      <section className="left-panel__section">
        <h3 className="left-panel__header">Connections</h3>
        <div className="left-panel__layers">
          {Object.entries(EDGE_LAYERS).map(([key, config]) => {
            const Icon = ICONS[key] || Link2;
            const isActive = filterState.edgeLayers.includes(key);

            return (
              <label key={key} className="left-panel__layer">
                <input
                  type="checkbox"
                  checked={isActive}
                  onChange={() => toggleEdgeLayer(key)}
                  className="left-panel__checkbox"
                />
                <Icon
                  size={14}
                  className="left-panel__layer-icon"
                  style={{ color: isActive ? config.color : undefined }}
                />
                <span className="left-panel__layer-label">{config.label}</span>
              </label>
            );
          })}
        </div>
      </section>

      {/* Filters */}
      <section className="left-panel__section">
        <h3 className="left-panel__header">
          <SlidersHorizontal size={12} />
          Filters
        </h3>

        {/* Depth Control (for Explore view) */}
        {currentView === 'explore' && (
          <div className="left-panel__filter">
            <label className="left-panel__filter-label">
              Depth: {filterState.depth}
            </label>
            <input
              type="range"
              min={1}
              max={5}
              value={filterState.depth}
              onChange={(e) => setDepth(parseInt(e.target.value, 10))}
              className="left-panel__slider"
            />
          </div>
        )}

        {/* Min Weight */}
        <div className="left-panel__filter">
          <label className="left-panel__filter-label">
            Min Weight: {Math.round(filterState.minWeight * 100)}%
          </label>
          <input
            type="range"
            min={0}
            max={100}
            value={filterState.minWeight * 100}
            onChange={(e) => setMinWeight(parseInt(e.target.value, 10) / 100)}
            className="left-panel__slider"
          />
        </div>
      </section>

      {/* Layout Presets (for Map view) */}
      {currentView === 'map' && (
        <section className="left-panel__section">
          <h3 className="left-panel__header">Layout</h3>
          <div className="left-panel__presets">
            {Object.entries(layout.presets).map(([key, preset]) => (
              <button
                key={key}
                className={`left-panel__preset ${layout.preset === key ? 'is-active' : ''}`}
                onClick={() => layout.changePreset(key)}
                title={preset.description}
              >
                {preset.name}
              </button>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

export default LeftPanel;
