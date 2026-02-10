/**
 * Brain section - LoRA adapter status and training
 */
import React, { useState, useEffect } from 'react';
import {
  Brain, ChevronUp, ChevronDown, Loader2, Database,
  Sparkles, Check, AlertCircle
} from 'lucide-react';
import { useBrain } from '../../hooks/useBrain';

function BrainSection() {
  const [isExpanded, setIsExpanded] = useState(true);
  const {
    status,
    adapters,
    isLoading,
    error,
    activeOperation,
    hasAdapter,
    activeVersion,
    brainStatus,
    notesIndexed,
    imagesIndexed,
    samplesCount,
    factsCount,
    lastIndexed,
    lastTrained,
    fetchStatus,
    fetchAdapters,
    startIndexing,
    startTraining,
    activateAdapter,
    formatDate,
    isIndexing,
    isTraining,
    canTrain,
    canIndex,
  } = useBrain();

  // Fetch status on mount
  useEffect(() => {
    fetchStatus();
    fetchAdapters();
  }, []);

  const handleIndex = async () => {
    try {
      await startIndexing(false);
    } catch (err) {
      console.error('Indexing failed:', err);
    }
  };

  const handleTrain = async () => {
    try {
      await startTraining();
    } catch (err) {
      console.error('Training failed:', err);
    }
  };

  const getStatusBadge = () => {
    switch (brainStatus) {
      case 'ready':
        return <span className="status-badge ready"><Check size={10} /> Ready</span>;
      case 'indexing':
        return <span className="status-badge indexing"><Loader2 size={10} className="spinning" /> Indexing</span>;
      case 'training':
        return <span className="status-badge training"><Loader2 size={10} className="spinning" /> Training</span>;
      case 'indexed':
        return <span className="status-badge indexed"><Database size={10} /> Indexed</span>;
      default:
        return <span className="status-badge none">Not Setup</span>;
    }
  };

  return (
    <div className="brain-section">
      <button
        className="section-header"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="section-title">
          <Brain size={14} />
          <span>Brain</span>
          {getStatusBadge()}
        </div>
        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {isExpanded && (
        <div className="brain-content">
          {error && (
            <div className="brain-error">
              <AlertCircle size={12} />
              {error}
            </div>
          )}

          {/* Progress bar during operations */}
          {activeOperation && (
            <div className="brain-progress">
              <div className="progress-bar">
                <div className="progress-bar-indeterminate" />
              </div>
              <span className="progress-text">
                {activeOperation.type === 'indexing' ? 'Indexing your content...' : 'Training your brain...'}
              </span>
            </div>
          )}

          {/* Stats */}
          <div className="brain-stats">
            <div className="brain-stat">
              <span className="stat-label">Adapter</span>
              <span className="stat-value">{hasAdapter ? `v${activeVersion}` : 'None'}</span>
            </div>
            <div className="brain-stat">
              <span className="stat-label">Notes</span>
              <span className="stat-value">{notesIndexed}</span>
            </div>
            <div className="brain-stat">
              <span className="stat-label">Images</span>
              <span className="stat-value">{imagesIndexed}</span>
            </div>
            <div className="brain-stat">
              <span className="stat-label">Samples</span>
              <span className="stat-value">{samplesCount}</span>
            </div>
            <div className="brain-stat">
              <span className="stat-label">Facts</span>
              <span className="stat-value">{factsCount}</span>
            </div>
          </div>

          {/* Timestamps */}
          <div className="brain-timestamps">
            <span>Indexed: {formatDate(lastIndexed)}</span>
            <span>Trained: {formatDate(lastTrained)}</span>
          </div>

          {/* Action buttons */}
          <div className="brain-actions">
            <button
              className="brain-action-btn index"
              onClick={handleIndex}
              disabled={!canIndex || isLoading}
              title="Analyze your notes and images to extract knowledge"
            >
              {isIndexing ? (
                <Loader2 size={14} className="spinning" />
              ) : (
                <Database size={14} />
              )}
              {isIndexing ? 'Indexing...' : 'Index'}
            </button>

            <button
              className="brain-action-btn train"
              onClick={handleTrain}
              disabled={!canTrain || isLoading}
              title={samplesCount === 0 ? 'Index first to generate training samples' : 'Train a personalized AI adapter'}
            >
              {isTraining ? (
                <Loader2 size={14} className="spinning" />
              ) : (
                <Sparkles size={14} />
              )}
              {isTraining ? 'Training...' : 'Train'}
            </button>
          </div>

          {/* Hint when no samples */}
          {samplesCount === 0 && !activeOperation && (
            <p className="brain-hint">
              Click "Index" to analyze your notes and generate training data.
            </p>
          )}

          {/* Adapters list */}
          {adapters.length > 0 && (
            <div className="brain-adapters">
              <div className="adapters-header">Adapters</div>
              {adapters.slice(0, 3).map((adapter) => (
                <div
                  key={adapter.version}
                  className={`adapter-item ${adapter.is_active ? 'active' : ''}`}
                  onClick={() => !adapter.is_active && activateAdapter(adapter.version)}
                >
                  <span className="adapter-version">
                    {adapter.is_active ? <Check size={12} /> : <span className="adapter-radio" />}
                    v{adapter.version}
                  </span>
                  <span className="adapter-info">{adapter.dataset_size} samples</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default BrainSection;
