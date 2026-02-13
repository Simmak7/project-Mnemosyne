/**
 * BrainFilesPanel - Shows brain files and topics for Mnemosyne mode
 */
import React, { useState, useEffect } from 'react';
import {
  Brain, FileText, ChevronUp, ChevronDown,
  Loader2, Sparkles, Check
} from 'lucide-react';
import { useAIChatContext } from '../../hooks/AIChatContext';
import { useMnemosyneBrain } from '../../hooks/useMnemosyneBrain';

function BrainFilesPanel() {
  const [isExpanded, setIsExpanded] = useState(true);
  const [viewingFile, setViewingFile] = useState(null);
  const [fileContent, setFileContent] = useState(null);
  const [loadingFile, setLoadingFile] = useState(false);
  const { state } = useAIChatContext();
  const {
    brainFiles, fetchBrainFiles, fetchBrainFile, fetchBrainStatus,
    hasBrain, isReady, isBuilding
  } = useMnemosyneBrain();

  useEffect(() => {
    fetchBrainStatus();
    fetchBrainFiles();
  }, []);

  const { brainFilesUsed, topicsMatched } = state;

  const handleViewFile = async (fileKey) => {
    if (viewingFile === fileKey) {
      setViewingFile(null);
      setFileContent(null);
      return;
    }
    setViewingFile(fileKey);
    setLoadingFile(true);
    try {
      const content = await fetchBrainFile(fileKey);
      setFileContent(content);
    } catch (err) {
      setFileContent({ error: err.message });
    } finally {
      setLoadingFile(false);
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
          <span>Brain Files</span>
          {isReady ? (
            <span className="status-badge ready"><Check size={10} /> Ready</span>
          ) : isBuilding ? (
            <span className="status-badge indexing"><Loader2 size={10} className="spinning" /> Building</span>
          ) : hasBrain ? (
            <span className="status-badge ready"><Check size={10} /> Built</span>
          ) : (
            <span className="status-badge none">Not Built</span>
          )}
        </div>
        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {isExpanded && (
        <div className="brain-content">
          {/* Files loaded for last response */}
          {brainFilesUsed.length > 0 && (
            <div className="brain-stats">
              <div className="adapters-header">Loaded Files</div>
              {brainFilesUsed.map((fileKey, idx) => (
                <div key={idx} className="adapter-item clickable" onClick={() => handleViewFile(fileKey)}>
                  <span className="adapter-version">
                    <FileText size={12} />
                    {fileKey}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Topics matched */}
          {topicsMatched.length > 0 && (
            <div className="brain-stats">
              <div className="adapters-header">Topics Matched</div>
              {topicsMatched.map((topic, idx) => (
                <div key={idx} className="adapter-item">
                  <span className="adapter-version">
                    <Sparkles size={12} />
                    {typeof topic === 'string' ? topic : topic.title || topic.key}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* All brain files */}
          {brainFiles.length > 0 && (
            <div className="brain-stats">
              <div className="adapters-header">All Brain Files ({brainFiles.length})</div>
              {brainFiles.map((file, idx) => (
                <div
                  key={idx}
                  className={`adapter-item clickable ${viewingFile === file.file_key ? 'active' : ''}`}
                  onClick={() => handleViewFile(file.file_key)}
                >
                  <span className="adapter-version">
                    <FileText size={12} />
                    {file.file_key}
                  </span>
                  <span className="adapter-info">
                    {file.file_type} · ~{file.token_count_approx || '?'} tokens
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* File content viewer */}
          {viewingFile && (
            <div className="brain-file-viewer">
              <div className="file-viewer-header">
                <span>{viewingFile}</span>
                <button onClick={() => { setViewingFile(null); setFileContent(null); }}>×</button>
              </div>
              <div className="file-viewer-content">
                {loadingFile ? (
                  <div className="loading"><Loader2 size={16} className="spinning" /> Loading...</div>
                ) : fileContent?.error ? (
                  <div className="error">{fileContent.error}</div>
                ) : fileContent?.content ? (
                  <pre>{fileContent.content}</pre>
                ) : (
                  <div className="empty">No content available</div>
                )}
              </div>
            </div>
          )}

          {!hasBrain && brainFiles.length === 0 && (
            <p className="brain-hint">
              Build your brain first to enable ZAIA AI mode.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export default BrainFilesPanel;
