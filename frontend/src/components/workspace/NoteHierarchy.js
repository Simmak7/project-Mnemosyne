import React, { useState, useEffect } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { ChevronDown, ChevronRight, Inbox, Calendar, Brain, FileQuestion, FileText } from 'lucide-react';
import { format } from 'date-fns';
import { useSmartBuckets } from '../../hooks/useSmartBuckets';
import { useWorkspaceState } from '../../hooks/useWorkspaceState';
import './NoteHierarchy.css';

/**
 * NoteHierarchy - Virtualized tree view of smart buckets
 * Buckets: Inbox, Daily Notes (Phase 5), AI Clusters (Phase 3), Orphans
 */
function NoteHierarchy() {
  const { allNotes, inboxNotes, dailyNotes, orphanNotes, aiClusters, loading, clustersLoading, clustersError } = useSmartBuckets();
  const { selectedNoteId, selectNote, clearNoteSelection } = useWorkspaceState();

  // Bucket collapse states (all start collapsed)
  const [inboxCollapsed, setInboxCollapsed] = useState(true);
  const [dailyCollapsed, setDailyCollapsed] = useState(true);
  const [clustersCollapsed, setClustersCollapsed] = useState(true);
  const [orphansCollapsed, setOrphansCollapsed] = useState(true);

  // Individual cluster collapse states
  const [clusterCollapseStates, setClusterCollapseStates] = useState({});

  // Cluster "show all" states (true = show all notes, false = show only 10)
  const [clusterShowAllStates, setClusterShowAllStates] = useState({});

  const parentRef = React.useRef(null);

  // Build flat list for virtualization
  const buildFlatList = () => {
    const items = [];

    // Inbox bucket
    items.push({ type: 'bucket', name: 'Inbox', icon: Inbox, collapsed: inboxCollapsed, toggle: () => setInboxCollapsed(!inboxCollapsed), count: inboxNotes.length });
    if (!inboxCollapsed) {
      inboxNotes.forEach(note => {
        items.push({ type: 'note', data: note, bucket: 'inbox' });
      });
    }

    // Daily Notes
    items.push({ type: 'bucket', name: 'Daily Notes', icon: Calendar, collapsed: dailyCollapsed, toggle: () => setDailyCollapsed(!dailyCollapsed), count: dailyNotes.length });
    if (!dailyCollapsed) {
      if (dailyNotes.length === 0) {
        items.push({ type: 'placeholder', message: 'No daily notes yet. Press Ctrl+Shift+D to create today\'s note!' });
      } else {
        dailyNotes.forEach(note => {
          items.push({ type: 'note', data: note, bucket: 'daily' });
        });
      }
    }

    // AI Clusters (Phase 3 - implemented!)
    const clusterCount = aiClusters.reduce((sum, cluster) => sum + cluster.size, 0);
    items.push({
      type: 'bucket',
      name: 'AI Clusters',
      icon: Brain,
      collapsed: clustersCollapsed,
      toggle: () => setClustersCollapsed(!clustersCollapsed),
      count: clusterCount,
      loading: clustersLoading,
      error: clustersError
    });

    if (!clustersCollapsed) {
      if (clustersLoading) {
        items.push({ type: 'placeholder', message: 'Loading clusters...' });
      } else if (clustersError) {
        items.push({ type: 'placeholder', message: clustersError, error: true });
      } else if (aiClusters.length === 0) {
        items.push({ type: 'placeholder', message: 'Not enough notes for clustering (need 10+)' });
      } else {
        // Add cluster items
        aiClusters.forEach((cluster) => {
          const clusterCollapsed = clusterCollapseStates[cluster.cluster_id] !== false; // Default collapsed
          items.push({
            type: 'cluster',
            data: cluster,
            collapsed: clusterCollapsed,
            toggle: () => setClusterCollapseStates(prev => ({
              ...prev,
              [cluster.cluster_id]: !clusterCollapsed
            }))
          });

          // If cluster is expanded, show its notes
          if (!clusterCollapsed && cluster.note_ids) {
            const showAll = clusterShowAllStates[cluster.cluster_id] === true;
            const notesToShow = showAll ? cluster.note_ids : cluster.note_ids.slice(0, 10);

            // Match note IDs with actual note data from ALL notes
            notesToShow.forEach(noteId => {
              // Find the note in allNotes (not just bucket notes)
              const note = allNotes.find(n => n.id === noteId);

              if (note) {
                items.push({ type: 'cluster-note', data: note, clusterId: cluster.cluster_id });
              } else {
                // Fallback if note not found (shouldn't happen)
                items.push({ type: 'cluster-note', noteId: noteId, clusterId: cluster.cluster_id });
              }
            });

            // Show "Show all X" or "Show less" button
            if (cluster.note_ids.length > 10) {
              items.push({
                type: 'show-more',
                clusterId: cluster.cluster_id,
                showAll: showAll,
                remaining: cluster.note_ids.length - 10,
                total: cluster.note_ids.length,
                toggle: () => setClusterShowAllStates(prev => ({
                  ...prev,
                  [cluster.cluster_id]: !showAll
                }))
              });
            }
          }
        });
      }
    }

    // Orphans bucket
    items.push({ type: 'bucket', name: 'Orphans', icon: FileQuestion, collapsed: orphansCollapsed, toggle: () => setOrphansCollapsed(!orphansCollapsed), count: orphanNotes.length });
    if (!orphansCollapsed) {
      orphanNotes.forEach(note => {
        items.push({ type: 'note', data: note, bucket: 'orphans' });
      });
    }

    return items;
  };

  const flatList = buildFlatList();

  // Virtualization
  const rowVirtualizer = useVirtualizer({
    count: flatList.length,
    getScrollElement: () => parentRef.current,
    estimateSize: (index) => {
      const item = flatList[index];
      if (item.type === 'bucket') return 44;
      if (item.type === 'note') return 40; // Compact single-line
      if (item.type === 'cluster') return 36;
      if (item.type === 'cluster-note') return 36; // Compact single-line
      if (item.type === 'placeholder') return 32;
      if (item.type === 'show-more') return 32;
      return 36;
    },
    overscan: 5,
  });

  const handleNoteClick = (note) => {
    selectNote(note.id);
  };

  const truncateTitle = (title, maxLength = 40) => {
    if (!title) return 'Untitled';
    return title.length > maxLength ? title.substring(0, maxLength) + '...' : title;
  };

  const handleJournalClick = () => {
    clearNoteSelection();
  };

  return (
    <div className="note-hierarchy">
      <div className="hierarchy-header">
        <h3>Notes</h3>
        <button
          className="journal-btn"
          onClick={handleJournalClick}
          title="Open Daily Journal"
        >
          <Calendar size={14} />
          <span>Journal</span>
        </button>
      </div>

      {loading ? (
        <div className="hierarchy-loading">
          <div className="loading-spinner"></div>
          <p>Loading notes...</p>
        </div>
      ) : (
        <div ref={parentRef} className="hierarchy-scroll-container">
          <div
            style={{
              height: `${rowVirtualizer.getTotalSize()}px`,
              width: '100%',
              position: 'relative',
            }}
          >
            {rowVirtualizer.getVirtualItems().map((virtualItem) => {
              const item = flatList[virtualItem.index];

              return (
                <div
                  key={virtualItem.index}
                  className={`hierarchy-item ${item.type === 'note' && item.data.id === selectedNoteId ? 'selected' : ''}`}
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: `${virtualItem.size}px`,
                    transform: `translateY(${virtualItem.start}px)`,
                  }}
                >
                  {item.type === 'bucket' && (
                    <div
                      className={`bucket-header ${item.placeholder ? 'placeholder' : ''}`}
                      onClick={item.toggle}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => e.key === 'Enter' && item.toggle()}
                    >
                      <span className="bucket-toggle">
                        {item.collapsed ? <ChevronRight size={16} /> : <ChevronDown size={16} />}
                      </span>
                      <item.icon size={16} className="bucket-icon" />
                      <span className="bucket-name">{item.name}</span>
                      <span className="bucket-count">{item.count}</span>
                    </div>
                  )}

                  {item.type === 'note' && (
                    <div
                      className="note-item"
                      onClick={() => handleNoteClick(item.data)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => e.key === 'Enter' && handleNoteClick(item.data)}
                    >
                      <FileText size={13} className="note-icon" />
                      <div className="note-content">
                        <span className="note-title">{truncateTitle(item.data.title)}</span>
                        <span className="note-date">
                          {format(new Date(item.data.created_at), 'MMM d')}
                        </span>
                      </div>
                    </div>
                  )}

                  {item.type === 'cluster' && (
                    <div
                      className="cluster-header"
                      data-cluster-id={item.data.cluster_id}
                      onClick={item.toggle}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => e.key === 'Enter' && item.toggle()}
                    >
                      <span className="bucket-toggle">
                        {item.collapsed ? <ChevronRight size={14} /> : <ChevronDown size={14} />}
                      </span>
                      <span className="cluster-emoji">{item.data.emoji}</span>
                      <span className="cluster-label">{item.data.label}</span>
                      <span className="cluster-count">{item.data.size}</span>
                    </div>
                  )}

                  {item.type === 'cluster-note' && (
                    <div
                      className="cluster-note-item"
                      onClick={() => selectNote(item.data ? item.data.id : item.noteId)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => e.key === 'Enter' && selectNote(item.data ? item.data.id : item.noteId)}
                    >
                      <FileText size={12} className="note-icon" />
                      <div className="cluster-note-content">
                        <span className="cluster-note-title">
                          {item.data ? truncateTitle(item.data.title, 35) : `Note #${item.noteId}`}
                        </span>
                        {item.data && (
                          <span className="cluster-note-date">
                            {format(new Date(item.data.created_at), 'MMM d, yyyy')}
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {item.type === 'placeholder' && (
                    <div className={`placeholder-message ${item.error ? 'error' : ''}`}>
                      {item.message}
                    </div>
                  )}

                  {item.type === 'show-more' && (
                    <div
                      className="show-more-btn"
                      onClick={item.toggle}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => e.key === 'Enter' && item.toggle()}
                    >
                      {item.showAll
                        ? `Show less`
                        : `Show all ${item.total} notes (+${item.remaining})`
                      }
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// Export without memo to allow re-renders when CSS loads
export default NoteHierarchy;
