import React from 'react';
import { X, Link2, Hash, Image, FileText, MousePointer2, ZoomIn, Move, Search } from 'lucide-react';
import './GraphHelp.css';

/**
 * Help modal for Knowledge Graph interactions
 * Explains how to build connections and interact with the graph
 */
function GraphHelp({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="graph-help-overlay" onClick={onClose}>
      <div className="graph-help-modal" onClick={(e) => e.stopPropagation()}>
        <div className="help-header">
          <h2>How to Use Your Knowledge Graph</h2>
          <button onClick={onClose} className="help-close-btn" aria-label="Close help">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="help-content">
          {/* Section 1: Building Connections */}
          <section className="help-section">
            <h3>
              <Link2 className="section-icon" />
              Building Connections
            </h3>
            <p className="section-intro">
              Your knowledge graph automatically builds as you create notes and upload images. Here's how to create connections:
            </p>

            <div className="help-cards">
              <div className="help-card">
                <div className="card-icon wikilink-icon">[[  ]]</div>
                <h4>Wikilinks</h4>
                <p>Connect notes by typing <code>[[Note Title]]</code> in your note content.</p>
                <div className="example">
                  <strong>Example:</strong>
                  <code>See also [[My Research Notes]] for more details.</code>
                </div>
              </div>

              <div className="help-card">
                <div className="card-icon tag-icon">
                  <Hash className="w-6 h-6" />
                </div>
                <h4>Tags</h4>
                <p>Categorize notes by adding <code>#tagname</code> anywhere in your note.</p>
                <div className="example">
                  <strong>Example:</strong>
                  <code>This is about #machinelearning and #python</code>
                </div>
              </div>

              <div className="help-card">
                <div className="card-icon image-icon">
                  <Image className="w-6 h-6" />
                </div>
                <h4>Images</h4>
                <p>Upload images - AI automatically creates linked notes with extracted content.</p>
                <div className="example">
                  <strong>Automatic:</strong> Image → AI Analysis → Note → Tags
                </div>
              </div>
            </div>
          </section>

          {/* Section 2: Interacting with the Graph */}
          <section className="help-section">
            <h3>
              <MousePointer2 className="section-icon" />
              Interacting with the Graph
            </h3>

            <div className="interaction-grid">
              <div className="interaction-item">
                <div className="interaction-icon">
                  <ZoomIn className="w-5 h-5" />
                </div>
                <div className="interaction-text">
                  <strong>Zoom:</strong> Scroll to zoom in/out
                </div>
              </div>

              <div className="interaction-item">
                <div className="interaction-icon">
                  <Move className="w-5 h-5" />
                </div>
                <div className="interaction-text">
                  <strong>Pan:</strong> Drag the background to move around
                </div>
              </div>

              <div className="interaction-item">
                <div className="interaction-icon">
                  <MousePointer2 className="w-5 h-5" />
                </div>
                <div className="interaction-text">
                  <strong>Move Nodes:</strong> Drag individual nodes to reposition
                </div>
              </div>

              <div className="interaction-item">
                <div className="interaction-icon">
                  <Search className="w-5 h-5" />
                </div>
                <div className="interaction-text">
                  <strong>Search:</strong> Type to find and highlight nodes
                </div>
              </div>
            </div>
          </section>

          {/* Section 3: Node Types */}
          <section className="help-section">
            <h3>
              <FileText className="section-icon" />
              Understanding Node Types
            </h3>

            <div className="node-types">
              <div className="node-type-item">
                <div className="node-preview note-node"></div>
                <div className="node-type-info">
                  <strong>Blue Circles - Notes</strong>
                  <p>Click to open the note in the Notes tab</p>
                </div>
              </div>

              <div className="node-type-item">
                <div className="node-preview tag-node"></div>
                <div className="node-type-info">
                  <strong>Orange Hexagons - Tags</strong>
                  <p>Click to filter notes by this tag</p>
                </div>
              </div>

              <div className="node-type-item">
                <div className="node-preview image-node"></div>
                <div className="node-type-info">
                  <strong>Green Circles - Images</strong>
                  <p>Click to view the image in the Gallery</p>
                </div>
              </div>
            </div>
          </section>

          {/* Section 4: Pro Tips */}
          <section className="help-section tips-section">
            <h3>Pro Tips</h3>
            <ul className="tips-list">
              <li>
                <strong>Create bidirectional links:</strong> Reference notes from multiple places to build a richer graph
              </li>
              <li>
                <strong>Use consistent tags:</strong> Reuse tag names to create tag clusters
              </li>
              <li>
                <strong>Hover for previews:</strong> Hover over nodes to see quick previews
              </li>
              <li>
                <strong>Use filters:</strong> Toggle node and link types to focus on specific connections
              </li>
              <li>
                <strong>Ask AI:</strong> Click "Ask AI" to get insights about your knowledge graph
              </li>
            </ul>
          </section>
        </div>

        <div className="help-footer">
          <button onClick={onClose} className="help-got-it-btn">
            Got it!
          </button>
        </div>
      </div>
    </div>
  );
}

export default GraphHelp;
