/**
 * RebuildPanel - Graph intelligence controls with user-friendly descriptions
 *
 * Explains what each AI operation does, shows stats, and provides
 * clear/reset controls so users can undo changes.
 */

import React, { useState } from 'react';
import { Brain, Network, Zap, ChevronDown, Loader2, Trash2 } from 'lucide-react';
import { useGraphRebuild, useSemanticStats, useCommunityStats } from '../hooks/useGraphRebuild';

export function RebuildPanel() {
  const [open, setOpen] = useState(false);
  const [threshold, setThreshold] = useState(0.85);
  const [confirmClear, setConfirmClear] = useState(false);

  const { semanticRebuild, clearSemantic, communityRebuild } = useGraphRebuild();
  const { data: semanticStats } = useSemanticStats();
  const { data: communityStats } = useCommunityStats();

  const anyLoading =
    semanticRebuild.isPending || communityRebuild.isPending || clearSemantic.isPending;

  return (
    <section className="left-panel__section rebuild-panel">
      <button className="rebuild-panel__header" onClick={() => setOpen(!open)}>
        <Brain size={12} />
        <span>Graph Intelligence</span>
        <ChevronDown size={14} className={`rebuild-panel__chevron ${open ? '' : 'is-rotated'}`} />
      </button>

      {open && (
        <div className="rebuild-panel__content">
          {/* Semantic Edges */}
          <div className="rebuild-panel__card">
            <div className="rebuild-panel__card-header">
              <Network size={14} />
              <span>AI Similarity Links</span>
            </div>
            <div className="rebuild-panel__description">
              Finds notes with similar content using AI embeddings and draws
              invisible connections between them. Higher threshold = fewer,
              stronger connections. Lower = more connections but noisier.
            </div>

            {semanticStats && (
              <div className="rebuild-panel__stats">
                <span>{semanticStats.semantic_edge_count} AI links</span>
                <span className="rebuild-panel__stats-sep">|</span>
                <span>{semanticStats.notes_with_embeddings} notes indexed</span>
              </div>
            )}

            <div className="rebuild-panel__threshold">
              <label className="rebuild-panel__label">
                Similarity: {Math.round(threshold * 100)}%
                <span className="rebuild-panel__label-hint">
                  {threshold >= 0.9 ? '(very strict)' : threshold >= 0.8 ? '(recommended)' : '(loose — may clutter)'}
                </span>
              </label>
              <input
                type="range" min={50} max={95} value={threshold * 100}
                onChange={(e) => setThreshold(parseInt(e.target.value, 10) / 100)}
                className="left-panel__slider"
              />
            </div>

            <div className="rebuild-panel__actions">
              <button
                className="rebuild-panel__btn"
                onClick={() => semanticRebuild.mutate({ threshold })}
                disabled={anyLoading}
              >
                {semanticRebuild.isPending
                  ? <><Loader2 size={14} className="is-spinning" /> Building...</>
                  : <><Network size={14} /> Generate Links</>}
              </button>

              {semanticStats?.semantic_edge_count > 0 && (
                confirmClear ? (
                  <div className="rebuild-panel__confirm">
                    <span>Remove all AI links?</span>
                    <button className="rebuild-panel__btn rebuild-panel__btn--danger"
                      onClick={() => { clearSemantic.mutate(); setConfirmClear(false); }}
                      disabled={anyLoading}>
                      Yes, clear
                    </button>
                    <button className="rebuild-panel__btn" onClick={() => setConfirmClear(false)}>
                      Cancel
                    </button>
                  </div>
                ) : (
                  <button
                    className="rebuild-panel__btn rebuild-panel__btn--secondary"
                    onClick={() => setConfirmClear(true)}
                    disabled={anyLoading}
                    title="Remove all AI-generated links and return to organic connections only"
                  >
                    <Trash2 size={14} /> Clear Links
                  </button>
                )
              )}
            </div>

            {semanticRebuild.isSuccess && (
              <div className="rebuild-panel__toast is-success">
                Started — links will appear after refresh
              </div>
            )}
            {clearSemantic.isSuccess && (
              <div className="rebuild-panel__toast is-success">
                AI links cleared — refresh to see changes
              </div>
            )}
            {(semanticRebuild.isError || clearSemantic.isError) && (
              <div className="rebuild-panel__toast is-error">
                {semanticRebuild.error?.message || clearSemantic.error?.message || 'Failed'}
              </div>
            )}
          </div>

          {/* Community Detection */}
          <div className="rebuild-panel__card">
            <div className="rebuild-panel__card-header">
              <Zap size={14} />
              <span>Auto-Clustering</span>
            </div>
            <div className="rebuild-panel__description">
              Groups related notes into clusters based on how they link
              to each other. Clusters appear as colors in Map view.
            </div>

            {communityStats && (
              <div className="rebuild-panel__stats">
                <span>{communityStats.community_count} clusters</span>
                <span className="rebuild-panel__stats-sep">|</span>
                <span>{communityStats.unclustered_count} unclustered</span>
              </div>
            )}

            <button
              className="rebuild-panel__btn"
              onClick={() => communityRebuild.mutate({ algorithm: 'louvain' })}
              disabled={anyLoading}
            >
              {communityRebuild.isPending
                ? <><Loader2 size={14} className="is-spinning" /> Detecting...</>
                : <><Zap size={14} /> Detect Clusters</>}
            </button>

            {communityRebuild.isSuccess && (
              <div className="rebuild-panel__toast is-success">
                Started — clusters will appear after refresh
              </div>
            )}
            {communityRebuild.isError && (
              <div className="rebuild-panel__toast is-error">
                {communityRebuild.error?.message || 'Failed'}
              </div>
            )}
          </div>

          <div className="rebuild-panel__hint">
            After running, click the refresh button in the graph toolbar to see changes.
          </div>
        </div>
      )}
    </section>
  );
}

export default RebuildPanel;
