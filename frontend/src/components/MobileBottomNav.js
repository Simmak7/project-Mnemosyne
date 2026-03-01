import React, { useState } from 'react';
import {
  LayoutDashboard, FileText, Image, Brain, Sparkles, Menu
} from 'lucide-react';
import MobileNavDrawer from './MobileNavDrawer';
import Settings from './Settings';
import { useSidebarConfig } from '../hooks/useSidebarConfig';
import './MobileBottomNav.css';

const PRIMARY_TABS = [
  { id: 'dashboard', icon: LayoutDashboard, label: 'Home' },
  { id: 'notes', icon: FileText, label: 'Notes' },
  { id: 'gallery', icon: Image, label: 'Gallery' },
  { id: 'graph', icon: Brain, label: 'Graph' },
  { id: 'chat', icon: Sparkles, label: 'AI' },
];

function MobileBottomNav({
  activeTab,
  onTabChange,
  username,
  onLogout,
  isDarkMode,
  onToggleDarkMode,
  onOpenSearch,
}) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const { isTabVisible } = useSidebarConfig();

  const visibleTabs = PRIMARY_TABS.filter(tab => isTabVisible(tab.id));

  const handleTabClick = (tabId) => {
    onTabChange(tabId);
  };

  return (
    <>
      <nav className="mobile-bottom-nav" aria-label="Main navigation">
        {visibleTabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              className={`mobile-nav-tab ${isActive ? 'active' : ''}`}
              onClick={() => handleTabClick(tab.id)}
              aria-label={tab.label}
              aria-current={isActive ? 'page' : undefined}
            >
              <Icon size={22} className="mobile-nav-icon" />
              <span className="mobile-nav-label">{tab.label}</span>
            </button>
          );
        })}

        <button
          className={`mobile-nav-tab ${drawerOpen ? 'active' : ''}`}
          onClick={() => setDrawerOpen(true)}
          aria-label="More options"
          aria-expanded={drawerOpen}
        >
          <Menu size={22} className="mobile-nav-icon" />
          <span className="mobile-nav-label">More</span>
        </button>
      </nav>

      <MobileNavDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        activeTab={activeTab}
        onTabChange={(tabId) => {
          onTabChange(tabId);
          setDrawerOpen(false);
        }}
        username={username}
        onLogout={onLogout}
        isDarkMode={isDarkMode}
        onToggleDarkMode={onToggleDarkMode}
        onOpenSearch={() => {
          onOpenSearch();
          setDrawerOpen(false);
        }}
        onOpenSettings={() => {
          setSettingsOpen(true);
          setDrawerOpen(false);
        }}
      />

      <Settings
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
      />
    </>
  );
}

export default MobileBottomNav;
