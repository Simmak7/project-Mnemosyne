/**
 * EdgeDetails - Edge inspector sub-component
 *
 * Shows "Why Connected?" info for selected edges including type,
 * strength, and evidence snippets.
 */

import React from 'react';
import { X } from 'lucide-react';
import { getEdgeLabel, getEdgeColor } from '../utils/edgeRendering';

export function EdgeDetails({ edge, onClose }) {
  const colors = getEdgeColor(edge);

  return (
    <>
      <div className="inspector__header">
        <h3 className="inspector__title">Connection</h3>
        <button className="inspector__close" onClick={onClose}>
          <X size={16} />
        </button>
      </div>

      <div
        className="inspector__type-badge"
        style={{ backgroundColor: colors.glow, color: colors.highlight }}
      >
        {edge.type}
      </div>

      <section className="inspector__section">
        <h4 className="inspector__section-title">Why Connected?</h4>
        <p className="inspector__excerpt">
          {getEdgeLabel(edge)}
        </p>
        {edge.weight && (
          <div className="inspector__meta-row">
            <span>Strength: {Math.round(edge.weight * 100)}%</span>
          </div>
        )}
      </section>

      {edge.evidence?.snippets?.length > 0 && (
        <section className="inspector__section">
          <h4 className="inspector__section-title">Evidence</h4>
          {edge.evidence.snippets.map((snippet, i) => (
            <p key={i} className="inspector__snippet">{snippet}</p>
          ))}
        </section>
      )}
    </>
  );
}

export default EdgeDetails;
