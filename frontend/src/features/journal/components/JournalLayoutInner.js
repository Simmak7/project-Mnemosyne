import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { ChevronRight, Calendar, Edit3, BarChart2 } from 'lucide-react';
import { format, addDays, subDays, parseISO } from 'date-fns';
import { useJournalContext } from '../hooks/JournalContext';
import { useIsMobile } from '../../../hooks/useIsMobile';
import { useSwipeNavigation } from '../../../hooks/useSwipeNavigation';
import MobilePanelTabs from '../../../components/MobilePanelTabs';
import { JournalSidebar } from './journal-sidebar';
import { JournalDayView } from './journal-day';
import { JournalInsights } from './journal-insights';
import './JournalLayout.css';

const MOBILE_PANELS = [
  { id: 'calendar', label: 'Calendar', icon: Calendar },
  { id: 'today', label: 'Today', icon: Edit3 },
  { id: 'insights', label: 'Insights', icon: BarChart2 },
];

const PANEL_IDS = MOBILE_PANELS.map(p => p.id);

/**
 * JournalLayoutInner - 3-pane resizable layout for Journal.
 * Keyboard: Left/Right arrows navigate days, T goes to today.
 */
function JournalLayoutInner({ onNavigateToNote, onNavigateToImage }) {
  const isMobile = useIsMobile();
  const [mobilePanel, setMobilePanel] = useState('today');
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const sidebarPanelRef = useRef(null);
  const { selectedDate, selectDate, navigateToToday } = useJournalContext();

  const swipeHandlers = useSwipeNavigation(PANEL_IDS, mobilePanel, setMobilePanel);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKey = (e) => {
      const tag = e.target.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || e.target.isContentEditable) return;

      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        const prev = format(subDays(parseISO(selectedDate), 1), 'yyyy-MM-dd');
        selectDate(prev);
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        const next = format(addDays(parseISO(selectedDate), 1), 'yyyy-MM-dd');
        selectDate(next);
      } else if (e.key === 't' || e.key === 'T') {
        navigateToToday();
      }
    };

    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [selectedDate, selectDate, navigateToToday]);

  const handleCollapseSidebar = useCallback(() => {
    sidebarPanelRef.current?.collapse();
  }, []);

  const handleExpandSidebar = useCallback(() => {
    sidebarPanelRef.current?.expand();
  }, []);

  // Mobile layout
  if (isMobile) {
    return (
      <div className="journal-layout ng-theme journal-layout--mobile">
        <MobilePanelTabs panels={MOBILE_PANELS} activePanel={mobilePanel} onPanelChange={setMobilePanel} />
        <div className="journal-mobile-content" {...swipeHandlers}>
          {mobilePanel === 'calendar' && (
            <JournalSidebar isCollapsed={false} onCollapse={() => {}} />
          )}
          {mobilePanel === 'today' && (
            <JournalDayView onNavigateToNote={onNavigateToNote} />
          )}
          {mobilePanel === 'insights' && (
            <JournalInsights onNavigateToNote={onNavigateToNote} />
          )}
        </div>
      </div>
    );
  }

  // Desktop layout (unchanged)
  return (
    <div className="journal-layout ng-theme">
      <PanelGroup direction="horizontal" className="journal-panel-group">
        <Panel
          ref={sidebarPanelRef}
          defaultSize={leftCollapsed ? 0 : 22}
          minSize={leftCollapsed ? 0 : 18}
          maxSize={30}
          collapsible={true}
          collapsedSize={0}
          onCollapse={() => setLeftCollapsed(true)}
          onExpand={() => setLeftCollapsed(false)}
          className="journal-panel journal-sidebar-panel"
          id="journal-sidebar"
        >
          <JournalSidebar
            isCollapsed={leftCollapsed}
            onCollapse={handleCollapseSidebar}
          />
        </Panel>

        {leftCollapsed && (
          <button
            className="journal-expand-floating"
            onClick={handleExpandSidebar}
            title="Expand sidebar"
          >
            <ChevronRight size={20} />
          </button>
        )}

        <PanelResizeHandle className="journal-resize-handle" />

        <Panel
          defaultSize={48}
          minSize={30}
          className="journal-panel journal-day-panel"
          id="journal-day"
        >
          <JournalDayView onNavigateToNote={onNavigateToNote} />
        </Panel>

        <PanelResizeHandle className="journal-resize-handle" />

        <Panel
          defaultSize={30}
          minSize={20}
          collapsible={true}
          collapsedSize={0}
          className="journal-panel journal-insights-panel"
          id="journal-insights"
        >
          <JournalInsights onNavigateToNote={onNavigateToNote} />
        </Panel>
      </PanelGroup>
    </div>
  );
}

export default JournalLayoutInner;
