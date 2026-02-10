/**
 * BrainStatusCard - Shows LoRA brain status and actions
 */
import React, { useEffect } from 'react';
import { Brain, Loader2, Database, Sparkles } from 'lucide-react';
import { useBrain } from '../../../hooks/useBrain';

function BrainStatusCard() {
  const {
    brainStatus,
    hasAdapter,
    activeVersion,
    samplesCount,
    isIndexing,
    isTraining,
    startIndexing,
    startTraining,
    fetchStatus,
    canTrain,
  } = useBrain();

  useEffect(() => {
    fetchStatus();
  }, []);

  const getStatusDisplay = () => {
    switch (brainStatus) {
      case 'ready':
        return { text: 'Ready', className: 'ready' };
      case 'indexing':
        return { text: 'Indexing...', className: 'indexing' };
      case 'training':
        return { text: 'Training...', className: 'training' };
      case 'indexed':
        return { text: 'Indexed', className: 'indexed' };
      default:
        return { text: 'Not Setup', className: '' };
    }
  };

  const statusDisplay = getStatusDisplay();

  const handleQuickAction = async () => {
    if (samplesCount === 0) {
      try {
        await startIndexing(false);
      } catch (err) {
        console.error('Indexing failed:', err);
      }
    } else if (canTrain) {
      try {
        await startTraining();
      } catch (err) {
        console.error('Training failed:', err);
      }
    }
  };

  const isOperating = isIndexing || isTraining;
  const buttonDisabled = isOperating || (hasAdapter && samplesCount === 0);

  return (
    <div className="brain-status-card">
      <div className="brain-status-header">
        <Brain size={16} />
        <span>Brain Status</span>
      </div>
      <div className="brain-status-content">
        <div className="brain-status-row">
          <span className="brain-status-label">Adapter:</span>
          <span className="brain-status-value">
            {hasAdapter ? `v${activeVersion}` : 'Base Model'}
          </span>
        </div>
        <div className="brain-status-row">
          <span className="brain-status-label">Status:</span>
          <span className={`brain-status-value ${statusDisplay.className}`}>
            {isOperating && <Loader2 size={12} className="spinning" />}
            {statusDisplay.text}
          </span>
        </div>
        {samplesCount > 0 && (
          <div className="brain-status-row">
            <span className="brain-status-label">Samples:</span>
            <span className="brain-status-value">{samplesCount}</span>
          </div>
        )}
      </div>
      <button
        className="brain-train-btn"
        onClick={handleQuickAction}
        disabled={buttonDisabled}
      >
        {isIndexing ? (
          <>
            <Loader2 size={14} className="spinning" />
            Indexing...
          </>
        ) : isTraining ? (
          <>
            <Loader2 size={14} className="spinning" />
            Training...
          </>
        ) : samplesCount === 0 ? (
          <>
            <Database size={14} />
            Index Brain
          </>
        ) : (
          <>
            <Sparkles size={14} />
            Train Brain
          </>
        )}
      </button>
    </div>
  );
}

export default BrainStatusCard;
