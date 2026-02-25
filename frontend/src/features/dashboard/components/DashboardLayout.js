/**
 * DashboardLayout - Free-form canvas dashboard with react-grid-layout
 *
 * Single unified grid with drag + resize in customize mode.
 */
import React, { useState, useCallback, useMemo } from 'react';
import { Responsive, useContainerWidth } from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

import { useDashboardData } from '../hooks/useDashboardData';
import { useDashboardConfig } from '../hooks/useDashboardConfig';
import { BREAKPOINTS, COLS, ROW_HEIGHT, MARGIN } from '../utils/defaultLayouts';

import DashboardHeader from './DashboardHeader';
import MetricsRow from './MetricsRow';
import QuickActions from './QuickActions';
import WidgetManager from './WidgetManager';

import BrainFocusWidget from './BrainFocusWidget';
import FavoriteImagesWidget from './FavoriteImagesWidget';
import QuickCaptureWidget from './QuickCaptureWidget';
import CalendarWidget from './CalendarWidget';
import KnowledgeGraphWidget from './KnowledgeGraphWidget';
import SystemStatusWidget from './SystemStatusWidget';
import RecentNotesWidget from './RecentNotesWidget';
import TopTagsWidget from './TopTagsWidget';
import MostConnectedWidget from './MostConnectedWidget';
import AIActivityWidget from './AIActivityWidget';
import TasksWidget from './TasksWidget';
import QuickUploadWidget from './QuickUploadWidget';

import './DashboardLayout.css';
import './Widgets.css';

function DashboardLayout({
  onNavigateToNote, onNavigateToImage, onNavigateToDocument,
  onNavigateToTag, onNavigateToSearch, onTabChange, onUploadSuccess,
}) {
  const { data, isLoading } = useDashboardData();
  const {
    layouts, visibleWidgets, isWidgetVisible, toggleWidget,
    onLayoutChange, resetToDefaults, isCustomizing, setIsCustomizing,
  } = useDashboardConfig();
  const [showWidgetManager, setShowWidgetManager] = useState(false);

  const { width: rawWidth, containerRef, mounted } = useContainerWidth();
  // Cap at 1200px to match dashboard-content max-width
  const width = Math.min(rawWidth, 1200);

  const renderWidget = useCallback((id) => {
    switch (id) {
      case 'brain-focus':
        return <BrainFocusWidget tags={data.tags} onNavigateToNote={onNavigateToNote}
          onNavigateToImage={onNavigateToImage} onTabChange={onTabChange} />;
      case 'quick-capture':
        return <QuickCaptureWidget onTabChange={onTabChange} />;
      case 'calendar':
        return <CalendarWidget onTabChange={onTabChange} />;
      case 'favorites':
        return <FavoriteImagesWidget favoriteImages={data.favoriteImages}
          isLoading={isLoading} onNavigateToImage={onNavigateToImage} onTabChange={onTabChange} />;
      case 'tasks':
        return <TasksWidget onTabChange={onTabChange} />;
      case 'quick-upload':
        return <QuickUploadWidget onTabChange={onTabChange} onUploadSuccess={onUploadSuccess} />;
      case 'knowledge-graph':
        return <KnowledgeGraphWidget graphStats={data.graphStats}
          isLoading={isLoading} onTabChange={onTabChange} />;
      case 'system-status':
        return <SystemStatusWidget health={data.health} gpuInfo={data.gpuInfo}
          embeddings={data.embeddings} brainStatus={data.brainStatus} isLoading={isLoading} />;
      case 'recent-notes':
        return <RecentNotesWidget recentNotes={data.recentNotes}
          isLoading={isLoading} onNavigateToNote={onNavigateToNote} onTabChange={onTabChange} />;
      case 'top-tags':
        return <TopTagsWidget tags={data.tags}
          isLoading={isLoading} onNavigateToTag={onNavigateToTag} onTabChange={onTabChange} />;
      case 'most-connected':
        return <MostConnectedWidget mostLinked={data.mostLinked}
          isLoading={isLoading} onNavigateToSearch={onNavigateToSearch} onTabChange={onTabChange} />;
      case 'ai-activity':
        return <AIActivityWidget brainStatus={data.brainStatus}
          ragConversations={data.ragConversations} isLoading={isLoading} onTabChange={onTabChange} />;
      default:
        return null;
    }
  }, [data, isLoading, onNavigateToNote, onNavigateToImage,
      onNavigateToTag, onNavigateToSearch, onTabChange, onUploadSuccess]);

  const children = useMemo(() =>
    visibleWidgets.map(id => (
      <div key={id} className={`grid-item ${isCustomizing ? 'grid-item--customizing' : ''}`}>
        {renderWidget(id)}
      </div>
    )),
    [visibleWidgets, isCustomizing, renderWidget]
  );

  return (
    <div className="dashboard-layout">
      <div className="dashboard-content">
        <DashboardHeader
          health={data.health}
          isCustomizing={isCustomizing}
          onEnterCustomize={() => setIsCustomizing(true)}
          onExitCustomize={() => setIsCustomizing(false)}
          onManageWidgets={() => setShowWidgetManager(true)}
        />
        <MetricsRow data={data} onTabChange={onTabChange} />
        <QuickActions onTabChange={onTabChange} />
      </div>

      <div className="dashboard-grid-wrapper" ref={containerRef}>
        {mounted && width > 0 && (
          <Responsive
            layouts={layouts}
            breakpoints={BREAKPOINTS}
            cols={COLS}
            width={width}
            rowHeight={ROW_HEIGHT}
            margin={MARGIN}
            containerPadding={[0, 0]}
            onLayoutChange={onLayoutChange}
            dragConfig={{
              enabled: isCustomizing,
            }}
            resizeConfig={{
              enabled: isCustomizing,
            }}
            className={`dashboard-grid ${isCustomizing ? 'dashboard-grid--customizing' : ''}`}
          >
            {children}
          </Responsive>
        )}
      </div>

      {showWidgetManager && (
        <WidgetManager
          isWidgetVisible={isWidgetVisible}
          toggleWidget={toggleWidget}
          resetToDefaults={resetToDefaults}
          onClose={() => setShowWidgetManager(false)}
        />
      )}
    </div>
  );
}

export default DashboardLayout;
