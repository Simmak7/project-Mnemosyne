import React, { useState, useCallback } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import GallerySidebar from './GallerySidebar';
import GalleryGrid from './GalleryGrid';
import GalleryContextPanel from './GalleryContextPanel';
import GallerySearchBar from './GallerySearchBar';
import { useGallerySearch } from '../hooks/useGalleryImages';
import './GalleryLayout.css';

/**
 * GalleryLayout - Main 3-column gallery container
 * 3-column layout with Neural Glass design
 *
 * Layout: [Sidebar | Photo Grid | Context Panel]
 */
function GalleryLayout({ onNavigateToNote, onNavigateToAI, selectedImageId, onClearSelection }) {
  // View state: 'all' | 'favorites' | 'trash' | 'album:{id}'
  const [currentView, setCurrentView] = useState('all');
  const [selectedAlbumId, setSelectedAlbumId] = useState(null);

  // Filter state
  const [selectedTags, setSelectedTags] = useState([]);
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');

  // View options
  const [rowHeight, setRowHeight] = useState(200);
  const [showFilenames, setShowFilenames] = useState(false);
  const [showDateHeaders, setShowDateHeaders] = useState(true);
  const [showTags, setShowTags] = useState(true);

  // Panel collapse state
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);

  // Search state
  const [searchType, setSearchType] = useState('text');
  const [isSearchMode, setIsSearchMode] = useState(false);
  const { search, searchResults, isSearching, clearResults } = useGallerySearch();

  // Handle view changes from sidebar
  const handleViewChange = useCallback((view, albumId = null) => {
    setCurrentView(view);
    setSelectedAlbumId(albumId);
    // Clear search when changing views
    setIsSearchMode(false);
    clearResults();
  }, [clearResults]);

  // Handle tag filter changes
  const handleTagsChange = useCallback((tags) => {
    setSelectedTags(tags);
  }, []);

  // Handle sort changes
  const handleSortChange = useCallback((field, order) => {
    setSortBy(field);
    setSortOrder(order);
  }, []);

  // Handle search
  const handleSearch = useCallback(async (query) => {
    try {
      await search({ query, searchType });
      setIsSearchMode(true);
    } catch (error) {
      console.error('Search failed:', error);
    }
  }, [search, searchType]);

  // Handle clear search
  const handleClearSearch = useCallback(() => {
    setIsSearchMode(false);
    clearResults();
  }, [clearResults]);

  return (
    <div className="gallery-layout ng-theme">
      {/* Search Bar - Fixed at top */}
      <div className="gallery-search-container">
        <GallerySearchBar
          onSearch={handleSearch}
          onClear={handleClearSearch}
          isSearching={isSearching}
          searchType={searchType}
          onSearchTypeChange={setSearchType}
          resultCount={isSearchMode ? searchResults.length : undefined}
        />
      </div>

      <PanelGroup direction="horizontal" className="gallery-panel-group">
        {/* Left Panel - Navigation Sidebar */}
        <Panel
          defaultSize={leftCollapsed ? 0 : 18}
          minSize={leftCollapsed ? 0 : 12}
          maxSize={25}
          collapsible={true}
          collapsedSize={0}
          onCollapse={() => setLeftCollapsed(true)}
          onExpand={() => setLeftCollapsed(false)}
          className="gallery-panel gallery-sidebar-panel"
          id="gallery-sidebar"
        >
          <GallerySidebar
            currentView={currentView}
            selectedAlbumId={selectedAlbumId}
            onViewChange={handleViewChange}
          />
        </Panel>

        <PanelResizeHandle className="gallery-resize-handle" />

        {/* Center Panel - Photo Grid */}
        <Panel
          defaultSize={64}
          minSize={40}
          className="gallery-panel gallery-grid-panel"
          id="gallery-grid"
        >
          <GalleryGrid
            currentView={currentView}
            selectedAlbumId={selectedAlbumId}
            selectedTags={selectedTags}
            sortBy={sortBy}
            sortOrder={sortOrder}
            rowHeight={rowHeight}
            showFilenames={showFilenames}
            showDateHeaders={showDateHeaders}
            showTags={showTags}
            onNavigateToNote={onNavigateToNote}
            onNavigateToAI={onNavigateToAI}
            isSearchMode={isSearchMode}
            searchResults={searchResults}
            selectedImageId={selectedImageId}
            onClearImageSelection={onClearSelection}
          />
        </Panel>

        <PanelResizeHandle className="gallery-resize-handle" />

        {/* Right Panel - Context (Tags, Sort, Options) */}
        <Panel
          defaultSize={rightCollapsed ? 0 : 18}
          minSize={rightCollapsed ? 0 : 14}
          maxSize={25}
          collapsible={true}
          collapsedSize={0}
          onCollapse={() => setRightCollapsed(true)}
          onExpand={() => setRightCollapsed(false)}
          className="gallery-panel gallery-context-panel"
          id="gallery-context"
        >
          <GalleryContextPanel
            selectedTags={selectedTags}
            onTagsChange={handleTagsChange}
            sortBy={sortBy}
            sortOrder={sortOrder}
            onSortChange={handleSortChange}
            rowHeight={rowHeight}
            onRowHeightChange={setRowHeight}
            showFilenames={showFilenames}
            onShowFilenamesChange={setShowFilenames}
            showDateHeaders={showDateHeaders}
            onShowDateHeadersChange={setShowDateHeaders}
            showTags={showTags}
            onShowTagsChange={setShowTags}
          />
        </Panel>
      </PanelGroup>
    </div>
  );
}

export default GalleryLayout;
