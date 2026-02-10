import React from 'react';

/**
 * Info panel showing graph statistics
 */
function GraphInfoPanel({ filteredGraphData }) {
  const noteCount = filteredGraphData.nodes.filter(n => n.type === 'note').length;
  const tagCount = filteredGraphData.nodes.filter(n => n.type === 'tag').length;
  const imageCount = filteredGraphData.nodes.filter(n => n.type === 'image').length;
  const linkCount = filteredGraphData.links.length;

  return (
    <div className="graph-info-panel">
      <h3>Knowledge Graph</h3>
      <div className="graph-stats">
        <div className="stat-item">
          <div className="stat-icon note-icon">📝</div>
          <div className="stat-content">
            <span className="stat-value">{noteCount}</span>
            <span className="stat-label">Notes</span>
          </div>
        </div>
        <div className="stat-item">
          <div className="stat-icon tag-icon">🏷️</div>
          <div className="stat-content">
            <span className="stat-value">{tagCount}</span>
            <span className="stat-label">Tags</span>
          </div>
        </div>
        <div className="stat-item">
          <div className="stat-icon image-icon">🖼️</div>
          <div className="stat-content">
            <span className="stat-value">{imageCount}</span>
            <span className="stat-label">Images</span>
          </div>
        </div>
        <div className="stat-item">
          <div className="stat-icon connection-icon">🔗</div>
          <div className="stat-content">
            <span className="stat-value">{linkCount}</span>
            <span className="stat-label">Connections</span>
          </div>
        </div>
      </div>
      <div className="graph-legend">
        <div className="legend-item">
          <div className="legend-color note-color"></div>
          <span>Notes</span>
        </div>
        <div className="legend-item">
          <div className="legend-color tag-color"></div>
          <span>Tags</span>
        </div>
        <div className="legend-item">
          <div className="legend-color image-color"></div>
          <span>Images</span>
        </div>
      </div>
    </div>
  );
}

export default GraphInfoPanel;
