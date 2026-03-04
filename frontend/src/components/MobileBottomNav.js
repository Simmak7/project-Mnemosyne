import React, { useState, useCallback } from 'react';
import {
  LayoutDashboard, FileText, Image, Brain, Sparkles, Menu
} from 'lucide-react';
import MobileNavDrawer from './MobileNavDrawer';
import MobileFAB from './MobileFAB';
import Settings from './Settings';
import { useSidebarConfig } from '../hooks/useSidebarConfig';
import './MobileBottomNav.css';

const PRIMARY_TABS = [
  { id: 'dashboard', icon: LayoutDashboard, label: 'Home', color: '#818cf8' },
  { id: 'notes', icon: FileText, label: 'Notes', color: '#fbbf24' },
  { id: 'gallery', icon: Image, label: 'Gallery', color: '#22d3ee' },
  { id: 'graph', icon: Brain, label: 'Graph', color: '#34d399' },
  { id: 'chat', icon: Sparkles, label: 'AI', color: '#a78bfa' },
];

const triggerHaptic = () => {
  if (navigator.vibrate) navigator.vibrate(8);
};

function MobileBottomNav({
  activeTab, onTabChange, username, onLogout, isDarkMode,
  onToggleDarkMode, onOpenSearch, isKeyboardOpen,
  isDrawerOpen, onOpenDrawer, onCloseDrawer,
}) {
  const [fallbackDrawer, setFallbackDrawer] = useState(false);
  const drawerOpen = isDrawerOpen ?? fallbackDrawer;
  const openDrawer = onOpenDrawer || (() => setFallbackDrawer(true));
  const closeDrawer = onCloseDrawer || (() => setFallbackDrawer(false));
  const [settingsOpen, setSettingsOpen] = useState(false);
  const { isTabVisible } = useSidebarConfig();

  const visibleTabs = PRIMARY_TABS.filter(tab => isTabVisible(tab.id));

  const handleTabClick = useCallback((tabId) => {
    triggerHaptic();
    onTabChange(tabId);
  }, [onTabChange]);

  return (
    <>
      <MobileFAB onTabChange={onTabChange} isKeyboardOpen={isKeyboardOpen} activeTab={activeTab} />

      <nav className={`mobile-bottom-nav${isKeyboardOpen ? ' keyboard-open' : ''}`} aria-label="Main navigation">
        {visibleTabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              className={`mobile-nav-tab ${isActive ? 'active' : ''}`}
              style={isActive ? { '--tab-color': tab.color } : undefined}
              onClick={() => handleTabClick(tab.id)}
              aria-label={tab.label}
              aria-current={isActive ? 'page' : undefined}
            >
              <Icon size={22} className="mobile-nav-icon" />
              <span className="mobile-nav-label">{tab.label}</span>
              {isActive && <span className="mobile-nav-glow" />}
            </button>
          );
        })}

        <button
          className={`mobile-nav-tab ${drawerOpen ? 'active' : ''}`}
          onClick={() => { triggerHaptic(); openDrawer(); }}
          aria-label="More options"
          aria-expanded={drawerOpen}
        >
          <Menu size={22} className="mobile-nav-icon" />
          <span className="mobile-nav-label">More</span>
        </button>
      </nav>

      <MobileNavDrawer
        isOpen={drawerOpen}
        onClose={closeDrawer}
        activeTab={activeTab}
        onTabChange={(tabId) => { onTabChange(tabId); closeDrawer(); }}
        username={username}
        onLogout={onLogout}
        isDarkMode={isDarkMode}
        onToggleDarkMode={onToggleDarkMode}
        onOpenSearch={() => { onOpenSearch(); closeDrawer(); }}
        onOpenSettings={() => { setSettingsOpen(true); closeDrawer(); }}
      />

      <Settings
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
      />
    </>
  );
}

export default MobileBottomNav;
