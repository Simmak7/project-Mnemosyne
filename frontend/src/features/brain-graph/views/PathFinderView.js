/**
 * PathFinderView - Find paths between two nodes
 *
 * Allows selecting start and end nodes, computes path,
 * and displays the path with edge type explanations.
 */

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Search, ArrowRight, Route, X } from 'lucide-react';

import { GraphCanvas } from '../components/GraphCanvas';
import { usePath, useGraphStats, useNodeSearch } from '../hooks/useGraphData';
import { getEdgeLabel } from '../utils/edgeRendering';

import './PathFinderView.css';

export function PathFinderView({ graphState, filters, layout }) {
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  // Source and target selection (initialize from context menu "Find Path From")
  const [sourceId, setSourceId] = useState(() => graphState.pathSourceId || '');
  const [targetId, setTargetId] = useState('');
  const [sourceSearch, setSourceSearch] = useState(() => graphState.pathSourceId || '');
  const [targetSearch, setTargetSearch] = useState('');
  const [showSourceDropdown, setShowSourceDropdown] = useState(false);
  const [showTargetDropdown, setShowTargetDropdown] = useState(false);

  // Search for nodes
  const { results: sourceResults } = useNodeSearch(sourceSearch);
  const { results: targetResults } = useNodeSearch(targetSearch);

  // Path finding
  const { data: pathData, isLoading, error, refetch } = usePath(
    sourceId || null,
    targetId || null
  );

  // Get stats for info
  const { data: stats } = useGraphStats();

  // Select a node from suggestions
  const selectSource = (node) => {
    setSourceId(node.id);
    setSourceSearch(node.title || node.id);
    setShowSourceDropdown(false);
  };

  const selectTarget = (node) => {
    setTargetId(node.id);
    setTargetSearch(node.title || node.id);
    setShowTargetDropdown(false);
  };

  // Resize handling
  useEffect(() => {
    if (!containerRef.current) return;

    const observer = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect;
      setDimensions({ width, height });
    });

    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // Build graph from path
  // Note: pathData.path is an array of node objects with id, type, title
  const graphData = useMemo(() => {
    if (!pathData?.path?.length) return null;

    // Path items can be strings (node IDs) or objects
    const nodes = pathData.path.map((item, index) => {
      // Handle both string IDs and node objects
      const nodeId = typeof item === 'string' ? item : item.id;
      const nodeTitle = typeof item === 'string'
        ? item
        : (item.title || item.id);
      const nodeType = typeof item === 'string'
        ? (nodeId.split('-')[0] || 'note')
        : (item.type || nodeId.split('-')[0] || 'note');

      return {
        id: nodeId,
        title: nodeTitle,
        type: nodeType,
        val: 2, // Highlight path nodes
        isPathNode: true,
        pathIndex: index,
      };
    });

    const links = [];
    for (let i = 0; i < nodes.length - 1; i++) {
      const edge = pathData.edges?.[i];
      links.push({
        source: nodes[i].id,
        target: nodes[i + 1].id,
        type: edge?.type || 'wikilink',
        weight: edge?.weight || 1,
      });
    }

    return { nodes, links };
  }, [pathData]);

  // Handle find path - uses hyphen format for node IDs (note-123, tag-456)
  const handleFindPath = () => {
    if (sourceSearch && !sourceId) {
      // If user entered a number, assume it's a note ID
      const isNumeric = /^\d+$/.test(sourceSearch.trim());
      setSourceId(isNumeric ? `note-${sourceSearch.trim()}` : sourceSearch);
    }
    if (targetSearch && !targetId) {
      const isNumeric = /^\d+$/.test(targetSearch.trim());
      setTargetId(isNumeric ? `note-${targetSearch.trim()}` : targetSearch);
    }
    refetch();
  };

  // Clear selections
  const clearSelection = (type) => {
    if (type === 'source') {
      setSourceId('');
      setSourceSearch('');
    } else {
      setTargetId('');
      setTargetSearch('');
    }
  };

  // Sync path source from context menu "Find Path From" action
  useEffect(() => {
    if (graphState.pathSourceId && graphState.pathSourceId !== sourceId) {
      setSourceId(graphState.pathSourceId);
      setSourceSearch(graphState.pathSourceId);
    }
  }, [graphState.pathSourceId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Use selected node as source/target
  useEffect(() => {
    if (graphState.selectedNode && !sourceId) {
      setSourceId(graphState.selectedNode.id);
      setSourceSearch(graphState.selectedNode.title || graphState.selectedNode.id);
    }
  }, [graphState.selectedNode, sourceId]);

  return (
    <div className="pathfinder-view" ref={containerRef}>
      {/* Search Panel */}
      <div className="pathfinder-view__panel">
        <h3 className="pathfinder-view__title">
          <Route size={16} />
          Find Path
        </h3>

        {/* Source Input */}
        <div className="pathfinder-view__field">
          <label className="pathfinder-view__label">From</label>
          <div className="pathfinder-view__input-wrap">
            <Search size={14} className="pathfinder-view__input-icon" />
            <input
              type="text"
              value={sourceSearch}
              onChange={(e) => {
                setSourceSearch(e.target.value);
                setSourceId('');
                setShowSourceDropdown(true);
              }}
              onFocus={() => setShowSourceDropdown(true)}
              onBlur={() => setTimeout(() => setShowSourceDropdown(false), 200)}
              placeholder="Search for a note..."
              className="pathfinder-view__input"
            />
            {sourceId && (
              <button
                className="pathfinder-view__clear"
                onClick={() => clearSelection('source')}
              >
                <X size={12} />
              </button>
            )}
            {/* Source Suggestions Dropdown */}
            {showSourceDropdown && sourceResults.length > 0 && (
              <div className="pathfinder-view__dropdown">
                {sourceResults.map((node) => (
                  <button
                    key={node.id}
                    className="pathfinder-view__dropdown-item"
                    onClick={() => selectSource(node)}
                  >
                    <span className="pathfinder-view__dropdown-title">{node.title}</span>
                    <span className="pathfinder-view__dropdown-type">{node.type}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
          {sourceId && (
            <span className="pathfinder-view__selected">{sourceId}</span>
          )}
        </div>

        {/* Arrow */}
        <div className="pathfinder-view__arrow">
          <ArrowRight size={20} />
        </div>

        {/* Target Input */}
        <div className="pathfinder-view__field">
          <label className="pathfinder-view__label">To</label>
          <div className="pathfinder-view__input-wrap">
            <Search size={14} className="pathfinder-view__input-icon" />
            <input
              type="text"
              value={targetSearch}
              onChange={(e) => {
                setTargetSearch(e.target.value);
                setTargetId('');
                setShowTargetDropdown(true);
              }}
              onFocus={() => setShowTargetDropdown(true)}
              onBlur={() => setTimeout(() => setShowTargetDropdown(false), 200)}
              placeholder="Search for a note..."
              className="pathfinder-view__input"
            />
            {targetId && (
              <button
                className="pathfinder-view__clear"
                onClick={() => clearSelection('target')}
              >
                <X size={12} />
              </button>
            )}
            {/* Target Suggestions Dropdown */}
            {showTargetDropdown && targetResults.length > 0 && (
              <div className="pathfinder-view__dropdown">
                {targetResults.map((node) => (
                  <button
                    key={node.id}
                    className="pathfinder-view__dropdown-item"
                    onClick={() => selectTarget(node)}
                  >
                    <span className="pathfinder-view__dropdown-title">{node.title}</span>
                    <span className="pathfinder-view__dropdown-type">{node.type}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
          {targetId && (
            <span className="pathfinder-view__selected">{targetId}</span>
          )}
        </div>

        {/* Find Button */}
        <button
          className="pathfinder-view__button"
          onClick={handleFindPath}
          disabled={isLoading || (!sourceId && !sourceSearch) || (!targetId && !targetSearch)}
        >
          {isLoading ? 'Finding...' : 'Find Path'}
        </button>

        {/* Error */}
        {error && (
          <div className="pathfinder-view__error">{error}</div>
        )}

        {/* Path Result */}
        {pathData?.path?.length > 0 && (
          <div className="pathfinder-view__result">
            <h4 className="pathfinder-view__result-title">
              Path Found ({pathData.path.length} steps)
            </h4>
            <div className="pathfinder-view__path">
              {pathData.path.map((node, i) => {
                const nodeId = typeof node === 'string' ? node : node.id;
                const nodeTitle = typeof node === 'string' ? node : (node.title || node.id);
                return (
                  <React.Fragment key={nodeId || i}>
                    <div className="pathfinder-view__node">
                      {nodeTitle}
                    </div>
                    {i < pathData.path.length - 1 && (
                      <div className="pathfinder-view__edge">
                        <ArrowRight size={12} />
                        <span>{getEdgeLabel(pathData.edges?.[i])}</span>
                      </div>
                    )}
                  </React.Fragment>
                );
              })}
            </div>
          </div>
        )}

        {/* No Path */}
        {pathData && !pathData.path?.length && !isLoading && (
          <div className="pathfinder-view__no-path">
            No path found between these nodes
          </div>
        )}
      </div>

      {/* Graph Canvas */}
      {graphData && (
        <GraphCanvas
          graphData={graphData}
          graphState={graphState}
          layout={layout}
          filters={filters}
          width={dimensions.width - 320}
          height={dimensions.height}
        />
      )}

      {/* Empty State */}
      {!graphData && !isLoading && (
        <div className="pathfinder-view__empty">
          <Route size={48} className="pathfinder-view__empty-icon" />
          <p>Select two nodes to find a path</p>
          <p className="pathfinder-view__empty-hint">
            Use the search or click nodes in Explore view first
          </p>
        </div>
      )}
    </div>
  );
}

export default PathFinderView;
