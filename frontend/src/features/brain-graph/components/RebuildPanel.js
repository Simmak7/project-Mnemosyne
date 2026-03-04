/**
 * RebuildPanel - Graph intelligence controls with user-friendly descriptions
 *
 * Explains what each AI operation does, shows stats, and provides
 * clear/reset controls so users can undo changes.
 */

import React, { useState } from 'react';
import { Brain, Network, Zap, ChevronDown, Loader2, Trash2, Sparkles } from 'lucide-react';
import { useGraphRebuild, useSemanticStats, useCommunityStats } from '../hooks/useGraphRebuild';

export function RebuildPanel() {
  const [open, setOpen] = useState(false);
  const [threshold, setThreshold] = useState(0.75);
  const [confirmClear, setConfirmClear] = useState(false);

  const { semanticRebuild, clearSemantic, communityRebuild, fullRebuild } = useGraphRebuild();
  const { data: semanticStats } = useSemanticStats();
  const { data: communityStats } = useCommunityStats();

  const anyLoading =
    semanticRebuild.isPending || communityRebuild.isPending ||
    clearSemantic.isPending || fullRebuild.isPending;

  return (
    <section className="left-panel__section rebuild-panel">
      <button className="rebuild-panel__header" onClick={() => setOpen(!open)}>
        <Brain size={12} />
        <span>Graph Intelligence</span>
        <ChevronDown size={14} className={`rebuild-panel__chevron ${open ? '' : 'is-rotated'}`} />
      </button>

      {open && (
        <div className="rebuild-panel__content">
          {/* Quick Full Analysis */}
          <div className="rebuild-panel__card rebuild-panel__card--featured">
            <div className="rebuild-panel__card-header">
              <Sparkles size={14} />
              <span>Full Analysis</span>
            </div>
            <div className="rebuild-panel__description">
              Runs both AI similarity links and cluster detection in one step.
              Best to run after adding new notes.
            </div>
            <button
              className="rebuild-panel__btn rebuild-panel__btn--primary"
              onClick={() => fullRebuild.mutate({ includeSemantic: true, includeClustering: true })}
              disabled={anyLoading}
            >
              {fullRebuild.isPending
                ? <><Loader2 size={14} className="is-spinning" /> Analysing...</>
                : <><Sparkles size={14} /> Analyse Graph</>}
            </button>
            {fullRebuild.isSuccess && (
              <div className="rebuild-panel__toast is-success">
                Analysis started — refresh Map view to see clusters and links
              </div>
            )}
            {fullRebuild.isError && (
              <div className="rebuild-panel__toast is-error">
                {fullRebuild.error?.message || 'Failed'}
              </div>
            )}
          </div>

          {/* Semantic Edges */}
          <div className="rebuild-panel__card">
            <div className="rebuild-panel__card-header">
              <Network size={14} />
              <span>AI Similarity Links</span>
            </div>
            <div className="rebuild-panel__description">
              Connects notes with similar content. Lower threshold finds more
              connections; raise it if the graph looks too cluttered.
            </div>

            {semanticStats && (
              <div className="rebuild-panel__stats">
                <span>{semanticStats.semantic_edge_count} AI links</span>
                <span className="rebuild-panel__stats-sep">·</span>
                <span>{semanticStats.notes_with_embeddings} notes indexed</span>
              </div>
            )}

            <div className="rebuild-panel__threshold">
              <label className="rebuild-panel__label">
                Threshold: {Math.round(threshold * 100)}%
                <span className="rebuild-panel__label-hint">
                  {threshold >= 0.9 ? '(strict)' : threshold >= 0.8 ? '(balanced)' : threshold >= 0.7 ? '(recommended)' : '(loose)'}
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
                    title="Remove all AI-generated links"
                  >
                    <Trash2 size={14} /> Clear Links
                  </button>
                )
              )}
            </div>

            {semanticRebuild.isSuccess && (
              <div className="rebuild-panel__toast is-success">
                Started — refresh to see new connections
              </div>
            )}
            {clearSemantic.isSuccess && (
              <div className="rebuild-panel__toast is-success">
                AI links cleared
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
              <span>Cluster Detection</span>
            </div>
            <div className="rebuild-panel__description">
              Groups related notes by link patterns. Results appear as
              colour-coded clusters in Map view with topic labels.
            </div>

            {communityStats && (
              <div className="rebuild-panel__stats">
                <span>{communityStats.community_count} clusters found</span>
                {communityStats.unclustered_count > 0 && (
                  <>
                    <span className="rebuild-panel__stats-sep">·</span>
                    <span>{communityStats.unclustered_count} solo notes</span>
                  </>
                )}
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
                Clusters detected — refresh Map view to see them
              </div>
            )}
            {communityRebuild.isError && (
              <div className="rebuild-panel__toast is-error">
                {communityRebuild.error?.message || 'Failed'}
              </div>
            )}
          </div>

          <div className="rebuild-panel__hint">
            After running, use the refresh button in the graph view to apply changes.
          </div>
        </div>
      )}
    </section>
  );
}

export default RebuildPanel;
