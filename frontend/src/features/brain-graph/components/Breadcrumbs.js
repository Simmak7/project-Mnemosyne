/**
 * Breadcrumbs - Navigation history trail for ExploreView
 *
 * Shows the path of focused nodes with back/forward buttons.
 * Each crumb is clickable to jump to that focus point.
 */

import React from 'react';
import { ChevronLeft, ChevronRight, ChevronRight as Sep } from 'lucide-react';
import './Breadcrumbs.css';

export function Breadcrumbs({ graphState, graphData }) {
  const history = graphState.getHistory();

  if (!history || history.stack.length <= 1) return null;

  // Resolve node titles from IDs using current graphData if available
  const resolveTitle = (nodeId) => {
    const node = graphData?.nodes?.find((n) => n.id === nodeId);
    if (node?.title) return node.title;
    // Fallback: format the ID nicely
    const [type, ...rest] = nodeId.split('-');
    return `${type} ${rest.join('-')}`;
  };

  // Show last 5 entries max
  const visible = history.stack.slice(-5);
  const offset = history.stack.length - visible.length;

  return (
    <div className="breadcrumbs">
      <button
        className="breadcrumbs__nav"
        onClick={graphState.navigateBack}
        disabled={!history.canGoBack}
        title="Go back (Alt+Left)"
      >
        <ChevronLeft size={14} />
      </button>

      <div className="breadcrumbs__trail">
        {visible.map((nodeId, i) => {
          const globalIndex = offset + i;
          const isCurrent = globalIndex === history.index;

          return (
            <React.Fragment key={`${nodeId}-${globalIndex}`}>
              {i > 0 && <Sep size={10} className="breadcrumbs__sep" />}
              <button
                className={`breadcrumbs__crumb ${isCurrent ? 'is-current' : ''}`}
                onClick={() => {
                  graphState.setFocusNodeId(nodeId);
                }}
                title={resolveTitle(nodeId)}
              >
                {truncate(resolveTitle(nodeId), 16)}
              </button>
            </React.Fragment>
          );
        })}
      </div>

      <button
        className="breadcrumbs__nav"
        onClick={graphState.navigateForward}
        disabled={!history.canGoForward}
        title="Go forward (Alt+Right)"
      >
        <ChevronRight size={14} />
      </button>
    </div>
  );
}

function truncate(text, maxLen) {
  if (!text || text.length <= maxLen) return text;
  return text.slice(0, maxLen - 1) + '\u2026';
}

export default Breadcrumbs;
