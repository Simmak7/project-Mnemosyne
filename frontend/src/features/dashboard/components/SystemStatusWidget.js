/**
 * SystemStatusWidget - Health, GPU, embeddings, brain status
 */
import React from 'react';
import { Activity } from 'lucide-react';
import WidgetShell from './WidgetShell';

function StatusRow({ label, ok, detail }) {
  const dotClass = ok === true ? 'status-ok' : ok === false ? 'status-error' : 'status-unknown';
  return (
    <div className="widget-status-row">
      <span className={`widget-status-dot ${dotClass}`} />
      <span className="widget-status-label">{label}</span>
      {detail && <span className="widget-status-detail">{detail}</span>}
    </div>
  );
}

function SystemStatusWidget({ health, gpuInfo, embeddings, brainStatus, isLoading }) {
  const svc = health?.components || health?.services || {};
  const ollamaOk = svc.ollama === 'connected' || health?.ollama === 'ok';
  const dbOk = svc.database === 'connected' || health?.database === 'ok';
  const redisOk = svc.redis === 'connected' || health?.redis === 'ok';

  const vram = gpuInfo?.vram_used_gb != null
    ? `${gpuInfo.vram_used_gb.toFixed(1)}G / ${(gpuInfo.vram_total_gb || 0).toFixed(1)}G`
    : gpuInfo?.gpu_name || null;

  const embPct = embeddings?.coverage_percent ?? embeddings?.percentage;
  const embeddingDisplay = embPct != null ? Math.round(embPct) : null;

  const brainTrained = brainStatus?.is_trained || brainStatus?.trained;

  return (
    <WidgetShell icon={Activity} title="System Status" isLoading={isLoading}>
      <div className="widget-status-list">
        <StatusRow label="Ollama" ok={health ? ollamaOk : undefined} />
        <StatusRow label="Database" ok={health ? dbOk : undefined} />
        <StatusRow label="Redis" ok={health ? redisOk : undefined} />
        {vram && <StatusRow label="GPU" ok={true} detail={vram} />}
      </div>

      {embeddingDisplay != null && (
        <div className="widget-progress-section">
          <div className="widget-progress-header">
            <span className="widget-progress-label">Embeddings</span>
            <span className="widget-progress-pct">{embeddingDisplay}%</span>
          </div>
          <div className="widget-progress-track">
            <div
              className="widget-progress-fill"
              style={{ width: `${embeddingDisplay}%` }}
            />
          </div>
        </div>
      )}

      {brainStatus && (
        <div className="widget-status-row" style={{ marginTop: 8 }}>
          <span className={`widget-status-dot ${brainTrained ? 'status-ok' : 'status-unknown'}`} />
          <span className="widget-status-label">Brain</span>
          <span className="widget-status-detail">
            {brainTrained ? 'Trained' : 'Not trained'}
          </span>
        </div>
      )}
    </WidgetShell>
  );
}

export default SystemStatusWidget;
