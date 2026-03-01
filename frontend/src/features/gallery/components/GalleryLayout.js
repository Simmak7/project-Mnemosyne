import React, { useState, useCallback } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { FolderOpen, Grid3X3, SlidersHorizontal } from 'lucide-react';
import { useIsMobile } from '../../../hooks/useIsMobile';
import { useSwipeNavigation } from '../../../hooks/useSwipeNavigation';
import MobilePanelTabs from '../../../components/MobilePanelTabs';
import GallerySidebar from './GallerySidebar';
import GalleryGrid from './GalleryGrid';
import GalleryContextPanel from './GalleryContextPanel';
import GallerySearchBar from './GallerySearchBar';
import { useGallerySearch } from '../hooks/useGalleryImages';
import './GalleryLayout.css';

const MOBILE_PANELS = [
  { id: 'albums', label: 'Albums', icon: FolderOpen },
  { id: 'photos', label: 'Photos', icon: Grid3X3 },
  { id: 'info', label: 'Filters', icon: SlidersHorizontal },
];

const PANEL_IDS = MOBILE_PANELS.map(p => p.id);

/**
 * GalleryLayout - Main 3-column gallery container
 */
function GalleryLayout({ onNavigateToNote, onNavigateToAI, selectedImageId, onClearSelection }) {
  const isMobile = useIsMobile();
  const [mobilePanel, setMobilePanel] = useState('photos');

  const [currentView, setCurrentView] = useState('all');
  const [selectedAlbumId, setSelectedAlbumId] = useState(null);
  const [selectedTags, setSelectedTags] = useState([]);
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');
  const [rowHeight, setRowHeight] = useState(isMobile ? 140 : 200);
  const [showFilenames, setShowFilenames] = useState(false);
  const [showDateHeaders, setShowDateHeaders] = useState(true);
  const [showTags, setShowTags] = useState(true);
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);
  const [searchType, setSearchType] = useState('text');
  const [isSearchMode, setIsSearchMode] = useState(false);
  const { search, searchResults, isSearching, clearResults } = useGallerySearch();

  const swipeHandlers = useSwipeNavigation(PANEL_IDS, mobilePanel, setMobilePanel);

  const handleViewChange = useCallback((view, albumId = null) => {
    setCurrentView(view);
    setSelectedAlbumId(albumId);
    setIsSearchMode(false);
    clearResults();
    if (isMobile) setMobilePanel('photos');
  }, [clearResults, isMobile]);

  const handleTagsChange = useCallback((tags) => setSelectedTags(tags), []);
  const handleSortChange = useCallback((field, order) => {
    setSortBy(field);
    setSortOrder(order);
  }, []);

  const handleSearch = useCallback(async (query) => {
    try {
      await search({ query, searchType });
      setIsSearchMode(true);
    } catch (error) {
      console.error('Search failed:', error);
    }
  }, [search, searchType]);

  const handleClearSearch = useCallback(() => {
    setIsSearchMode(false);
    clearResults();
  }, [clearResults]);

  const gridProps = {
    currentView, selectedAlbumId, selectedTags, sortBy, sortOrder,
    rowHeight: isMobile ? 140 : rowHeight,
    showFilenames, showDateHeaders, showTags,
    onNavigateToNote, onNavigateToAI, isSearchMode, searchResults,
    selectedImageId, onClearImageSelection: onClearSelection,
  };

  const contextProps = {
    selectedTags, onTagsChange: handleTagsChange,
    sortBy, sortOrder, onSortChange: handleSortChange,
    rowHeight, onRowHeightChange: setRowHeight,
    showFilenames, onShowFilenamesChange: setShowFilenames,
    showDateHeaders, onShowDateHeadersChange: setShowDateHeaders,
    showTags, onShowTagsChange: setShowTags,
  };

  // Mobile layout
  if (isMobile) {
    return (
      <div className="gallery-layout ng-theme gallery-layout--mobile">
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
        <MobilePanelTabs panels={MOBILE_PANELS} activePanel={mobilePanel} onPanelChange={setMobilePanel} />
        <div className="gallery-mobile-content" {...swipeHandlers}>
          {mobilePanel === 'albums' && (
            <GallerySidebar
              currentView={currentView}
              selectedAlbumId={selectedAlbumId}
              onViewChange={handleViewChange}
            />
          )}
          {mobilePanel === 'photos' && <GalleryGrid {...gridProps} />}
          {mobilePanel === 'info' && <GalleryContextPanel {...contextProps} />}
        </div>
      </div>
    );
  }

  // Desktop layout (unchanged)
  return (
    <div className="gallery-layout ng-theme">
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

        <Panel
          defaultSize={64}
          minSize={40}
          className="gallery-panel gallery-grid-panel"
          id="gallery-grid"
        >
          <GalleryGrid {...gridProps} />
        </Panel>

        <PanelResizeHandle className="gallery-resize-handle" />

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
          <GalleryContextPanel {...contextProps} />
        </Panel>
      </PanelGroup>
    </div>
  );
}

export default GalleryLayout;
