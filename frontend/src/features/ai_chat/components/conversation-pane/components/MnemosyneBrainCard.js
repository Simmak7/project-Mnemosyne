/**
 * MnemosyneBrainCard - Shows Mnemosyne brain status and build actions
 */
import React, { useEffect } from 'react';
import { Brain, Loader2, Database, Sparkles } from 'lucide-react';
import { useMnemosyneBrain } from '../../../hooks/useMnemosyneBrain';

function MnemosyneBrainCard() {
  const {
    hasBrain, isReady, isBuilding, isStale,
    fetchBrainStatus, triggerBuild,
    buildStatus,
  } = useMnemosyneBrain();

  useEffect(() => {
    fetchBrainStatus();
  }, []);

  const getStatusDisplay = () => {
    if (isBuilding) return { text: 'Building...', className: 'indexing' };
    if (isStale) return { text: 'Stale', className: 'indexed' };
    if (isReady) return { text: 'Ready', className: 'ready' };
    if (hasBrain) return { text: 'Built', className: 'ready' };
    return { text: 'Not Built', className: '' };
  };

  const statusDisplay = getStatusDisplay();

  const handleBuild = async () => {
    try {
      await triggerBuild(true);
    } catch (err) {
      console.error('Brain build failed:', err);
    }
  };

  return (
    <div className="brain-status-card">
      <div className="brain-status-header">
        <Brain size={16} />
        <span>Muse Brain</span>
      </div>
      <div className="brain-status-content">
        <div className="brain-status-row">
          <span className="brain-status-label">Status:</span>
          <span className={`brain-status-value ${statusDisplay.className}`}>
            {isBuilding && <Loader2 size={12} className="spinning" />}
            {statusDisplay.text}
          </span>
        </div>
        {buildStatus?.progress_pct > 0 && isBuilding && (
          <div className="brain-status-row">
            <span className="brain-status-label">Progress:</span>
            <span className="brain-status-value">{buildStatus.progress_pct}%</span>
          </div>
        )}
      </div>
      <button
        className="brain-train-btn"
        onClick={handleBuild}
        disabled={isBuilding}
      >
        {isBuilding ? (
          <>
            <Loader2 size={14} className="spinning" />
            Building...
          </>
        ) : isStale ? (
          <>
            <Sparkles size={14} />
            Rebuild Brain
          </>
        ) : hasBrain ? (
          <>
            <Sparkles size={14} />
            Rebuild Brain
          </>
        ) : (
          <>
            <Database size={14} />
            Build Brain
          </>
        )}
      </button>
    </div>
  );
}

export default MnemosyneBrainCard;
