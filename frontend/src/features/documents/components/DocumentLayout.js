/**
 * DocumentLayout - Main 2-panel container for Documents view
 * Left: DocumentList with filters, collections, search, sort
 * Right: ReviewPanel or DocumentViewer
 */

import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import {
  FileScan, Eye, CheckCircle, AlertCircle, FolderOpen,
  ChevronDown, ChevronRight, Plus, Trash2, Check, X,
  List, FileText,
} from 'lucide-react';

import { useIsMobile } from '../../../hooks/useIsMobile';
import { useSwipeNavigation } from '../../../hooks/useSwipeNavigation';
import MobilePanelTabs from '../../../components/MobilePanelTabs';
import DocumentList from './DocumentList';
import ReviewPanel from './ReviewPanel';
import DocumentViewer from './DocumentViewer';
import { useDocuments } from '../hooks/useDocuments';
import { useCollections } from '../../notes/hooks/useCollections';

import './DocumentLayout.css';

const STATUS_FILTERS = [
  { key: null, label: 'All', icon: null, color: 'neutral' },
  { key: 'needs_review', label: 'Needs Review', icon: Eye, color: 'amber' },
  { key: 'completed', label: 'Completed', icon: CheckCircle, color: 'green' },
  { key: 'failed', label: 'Failed', icon: AlertCircle, color: 'red' },
];

const SORT_OPTIONS = [
  { key: 'uploaded_at', label: 'Date Uploaded' },
  { key: 'name', label: 'Name' },
  { key: 'file_size', label: 'File Size' },
  { key: 'page_count', label: 'Pages' },
  { key: 'status', label: 'Status' },
];

const GROUP_OPTIONS = [
  { key: null, label: 'None' },
  { key: 'status', label: 'By Status' },
  { key: 'document_type', label: 'By Type' },
];

const MOBILE_PANELS = [
  { id: 'list', label: 'List', icon: List },
  { id: 'review', label: 'Review', icon: FileText },
];

const PANEL_IDS = MOBILE_PANELS.map(p => p.id);

function DocumentLayout({ onNavigateToNote, selectedDocumentId, onClearSelection }) {
  const isMobile = useIsMobile();
  const [mobilePanel, setMobilePanel] = useState('list');
  const [statusFilter, setStatusFilter] = useState(null);
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [viewMode, setViewMode] = useState('review');
  const [sortBy, setSortBy] = useState('uploaded_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [groupBy, setGroupBy] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCollectionId, setSelectedCollectionId] = useState(null);
  const [collectionsExpanded, setCollectionsExpanded] = useState(!isMobile);

  const { data, isLoading, error } = useDocuments(statusFilter, sortBy, sortOrder, selectedCollectionId);
  const documents = useMemo(() => data?.documents || [], [data]);

  const { collections, deleteCollection, createCollection, isCreating } = useCollections();

  const [showNewCollectionForm, setShowNewCollectionForm] = useState(false);
  const [newCollectionName, setNewCollectionName] = useState('');

  const swipeHandlers = useSwipeNavigation(PANEL_IDS, mobilePanel, setMobilePanel);

  const statusCounts = useMemo(() => {
    const counts = { all: documents.length, needs_review: 0, completed: 0, failed: 0 };
    for (const doc of documents) {
      const s = doc.ai_analysis_status;
      if (s === 'needs_review') counts.needs_review++;
      else if (s === 'completed') counts.completed++;
      else if (s === 'failed') counts.failed++;
    }
    return counts;
  }, [documents]);

  useEffect(() => {
    if (selectedDocumentId) {
      setSelectedDocId(selectedDocumentId);
      if (isMobile) setMobilePanel('review');
      if (onClearSelection) onClearSelection();
    }
  }, [selectedDocumentId, onClearSelection, isMobile]);

  const handleDocSelect = useCallback((docId) => {
    setSelectedDocId(docId);
    const doc = documents.find(d => d.id === docId);
    if (doc?.ai_analysis_status === 'needs_review') setViewMode('review');
    if (isMobile) setMobilePanel('review');
  }, [documents, isMobile]);

  const filteredDocs = useMemo(() => {
    if (!searchQuery.trim()) return documents;
    const q = searchQuery.toLowerCase();
    return documents.filter(d =>
      (d.display_name || d.filename || '').toLowerCase().includes(q) ||
      (d.document_type || '').toLowerCase().includes(q)
    );
  }, [documents, searchQuery]);

  const groupedDocs = useMemo(() => {
    if (!groupBy) return null;
    const groups = {};
    for (const doc of filteredDocs) {
      let key;
      if (groupBy === 'status') key = doc.ai_analysis_status || 'pending';
      else if (groupBy === 'document_type') key = doc.document_type || 'Unknown';
      else key = 'All';
      if (!groups[key]) groups[key] = [];
      groups[key].push(doc);
    }
    return groups;
  }, [filteredDocs, groupBy]);

  const handleSortToggle = useCallback((key) => {
    if (sortBy === key) setSortOrder(prev => prev === 'desc' ? 'asc' : 'desc');
    else { setSortBy(key); setSortOrder('desc'); }
  }, [sortBy]);

  const handleDeleteCollection = useCallback((e, collectionId) => {
    e.stopPropagation();
    if (window.confirm('Delete this collection? Documents will not be deleted.')) {
      deleteCollection(collectionId);
      if (selectedCollectionId === collectionId) setSelectedCollectionId(null);
    }
  }, [deleteCollection, selectedCollectionId]);

  const handleCreateCollection = useCallback((e) => {
    e.preventDefault();
    if (newCollectionName.trim()) {
      createCollection({ name: newCollectionName.trim() }, {
        onSuccess: () => { setNewCollectionName(''); setShowNewCollectionForm(false); }
      });
    }
  }, [newCollectionName, createCollection]);

  const selectedDoc = documents.find(d => d.id === selectedDocId);
  const getCountForFilter = (key) => !key ? statusCounts.all : statusCounts[key] || 0;

  const listPanel = (
    <div className="document-list-panel">
      <div className="document-filter-tabs">
        {STATUS_FILTERS.map(f => {
          const Icon = f.icon;
          const count = getCountForFilter(f.key);
          return (
            <button
              key={f.key || 'all'}
              className={`document-filter-tab document-filter-tab--${f.color} ${statusFilter === f.key ? 'active' : ''}`}
              onClick={() => setStatusFilter(f.key)}
            >
              {Icon && <Icon size={14} />}
              <span>{f.label}</span>
              <span className="filter-tab-count">{count}</span>
            </button>
          );
        })}
      </div>
      <div className="document-collections-section">
        <div className="collections-section-header-row">
          <button className="collections-section-header" onClick={() => setCollectionsExpanded(!collectionsExpanded)}>
            {collectionsExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            <span>Collections</span>
            {collections.length > 0 && <span className="collections-header-count">{collections.length}</span>}
          </button>
          <button className="collections-add-btn" onClick={(e) => { e.stopPropagation(); setCollectionsExpanded(true); setShowNewCollectionForm(true); }} title="New collection">
            <Plus size={13} />
          </button>
        </div>
        {collectionsExpanded && (
          <div className="collections-list">
            {collections.length > 0 && (
              <button className={`collection-item ${!selectedCollectionId ? 'active' : ''}`} onClick={() => setSelectedCollectionId(null)}>
                <FolderOpen size={14} /><span className="collection-item-name">All Documents</span>
              </button>
            )}
            {collections.map(c => (
              <button key={c.id} className={`collection-item ${selectedCollectionId === c.id ? 'active' : ''}`} onClick={() => setSelectedCollectionId(c.id)}>
                <span className="collection-item-icon">{c.icon || '\uD83D\uDCC1'}</span>
                <span className="collection-item-name">{c.name}</span>
                <span className="collection-doc-count">{c.document_count}</span>
                <button className="collection-item-delete" onClick={(e) => handleDeleteCollection(e, c.id)} title="Delete collection"><Trash2 size={12} /></button>
              </button>
            ))}
            {showNewCollectionForm && (
              <form className="collection-create-form" onSubmit={handleCreateCollection}>
                <input type="text" value={newCollectionName} onChange={(e) => setNewCollectionName(e.target.value)} placeholder="Collection name..." autoFocus className="collection-create-input" />
                <button type="submit" className="collection-create-btn confirm" disabled={!newCollectionName.trim() || isCreating} title="Create"><Check size={13} /></button>
                <button type="button" className="collection-create-btn cancel" onClick={() => { setShowNewCollectionForm(false); setNewCollectionName(''); }} title="Cancel"><X size={13} /></button>
              </form>
            )}
            {collections.length === 0 && !showNewCollectionForm && <div className="collections-empty-hint">No collections yet</div>}
          </div>
        )}
      </div>
      <div className="document-toolbar">
        <input type="text" className="document-search-input" placeholder="Search documents..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
        <div className="document-toolbar-controls">
          <select className="document-select" value={sortBy} onChange={e => handleSortToggle(e.target.value)} title="Sort by">
            {SORT_OPTIONS.map(o => <option key={o.key} value={o.key}>{o.label}</option>)}
          </select>
          <button className="document-sort-order" onClick={() => setSortOrder(prev => prev === 'desc' ? 'asc' : 'desc')} title={sortOrder === 'desc' ? 'Newest first' : 'Oldest first'}>
            {sortOrder === 'desc' ? '\u2193' : '\u2191'}
          </button>
          <select className="document-select" value={groupBy || ''} onChange={e => setGroupBy(e.target.value || null)} title="Group by">
            {GROUP_OPTIONS.map(o => <option key={o.key || 'none'} value={o.key || ''}>{o.label}</option>)}
          </select>
        </div>
      </div>
      <DocumentList documents={filteredDocs} groupedDocs={groupedDocs} isLoading={isLoading} error={error} selectedDocId={selectedDocId} onSelect={handleDocSelect} />
    </div>
  );

  const detailPanel = (
    <div className="document-detail-panel">
      {!selectedDoc ? (
        <div className="document-empty-state"><FileScan size={48} strokeWidth={1} /><p>Select a document to view details</p></div>
      ) : viewMode === 'viewer' ? (
        <DocumentViewer document={selectedDoc} />
      ) : (
        <ReviewPanel document={selectedDoc} onNavigateToNote={onNavigateToNote} />
      )}
    </div>
  );

  // Mobile layout
  if (isMobile) {
    return (
      <div className="document-layout ng-theme document-layout--mobile">
        <div className="document-header">
          <div className="document-header-title">
            <h1>Documents</h1>
            {data?.total > 0 && <span className="document-header-count">{data.total}</span>}
          </div>
        </div>
        <MobilePanelTabs panels={MOBILE_PANELS} activePanel={mobilePanel} onPanelChange={setMobilePanel} />
        <div className="document-mobile-content" {...swipeHandlers}>
          {mobilePanel === 'list' && listPanel}
          {mobilePanel === 'review' && detailPanel}
        </div>
      </div>
    );
  }

  // Desktop layout (unchanged)
  return (
    <div className="document-layout ng-theme">
      <div className="document-header">
        <div className="document-header-title">
          <h1>Documents</h1>
          {data?.total > 0 && <span className="document-header-count">{data.total}</span>}
        </div>
      </div>
      <PanelGroup direction="horizontal" className="document-panel-group">
        <Panel defaultSize={35} minSize={25} maxSize={50} id="doc-list">
          {listPanel}
        </Panel>
        <PanelResizeHandle className="document-resize-handle" />
        <Panel defaultSize={65} minSize={50} id="doc-detail">
          {detailPanel}
        </Panel>
      </PanelGroup>
    </div>
  );
}

export default DocumentLayout;
