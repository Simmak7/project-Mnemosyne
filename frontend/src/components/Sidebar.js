import React, { useState, useRef, useEffect } from 'react';
import { Brain, LogOut, Settings as SettingsIcon, ChevronUp, Search, Sparkles, Upload, Image, FileText, BookOpen, FileScan, Sun, Moon } from 'lucide-react';
import Settings from './Settings';
import './Sidebar.css';

function Sidebar({ activeTab, onTabChange, username, onLogout, isDarkMode, onToggleDarkMode, onOpenSearch }) {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const menuRef = useRef(null);
  const userSectionRef = useRef(null);

  // Feature flags
  const journalEnabled = localStorage.getItem('ENABLE_JOURNAL') !== 'false';
  const documentsEnabled = localStorage.getItem('ENABLE_DOCUMENTS') !== 'false';

  const navItems = [
    { id: 'upload', iconComponent: Upload, label: 'Studio' },
    { id: 'gallery', iconComponent: Image, label: 'Gallery' },
    ...(documentsEnabled ? [{ id: 'documents', iconComponent: FileScan, label: 'Documents' }] : []),
    { id: 'notes', iconComponent: FileText, label: 'Notes' },
    ...(journalEnabled ? [{ id: 'journal', iconComponent: BookOpen, label: 'Journal' }] : []),
    { id: 'graph', iconComponent: Brain, label: 'Brain' },
    { id: 'chat', iconComponent: Sparkles, label: 'Mnemos AIs' }
  ];

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        menuRef.current &&
        !menuRef.current.contains(event.target) &&
        userSectionRef.current &&
        !userSectionRef.current.contains(event.target)
      ) {
        setShowUserMenu(false);
      }
    };

    if (showUserMenu) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showUserMenu]);

  // Close dropdown when pressing Escape
  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        setShowUserMenu(false);
        setShowSettings(false);
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, []);

  const handleSettingsClick = () => {
    setShowUserMenu(false);
    setShowSettings(true);
  };

  const handleLogoutClick = () => {
    setShowUserMenu(false);
    onLogout();
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="logo">
          <div className="logo-monogram">M</div>
          <div className="logo-wordmark">MNEMOSYNE</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {/* Search button with special styling */}
        <button
          className="nav-item search-item"
          onClick={onOpenSearch}
          title="Search (Ctrl+K / Cmd+K)"
          aria-label="Open search (Ctrl+K or Cmd+K)"
        >
          <Search size={20} className="nav-icon-svg" />
          <span className="nav-label">Search</span>
          <kbd className="search-kbd">⌘K</kbd>
        </button>

        {navItems.map(item => (
          <button
            key={item.id}
            className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
            onClick={() => onTabChange(item.id)}
            aria-label={`Navigate to ${item.label}`}
            aria-current={activeTab === item.id ? 'page' : undefined}
          >
            {item.iconComponent ? (
              <item.iconComponent size={20} className="nav-icon-svg" />
            ) : (
              <span className="nav-icon">{item.icon}</span>
            )}
            <span className="nav-label">{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <button
          className="theme-toggle"
          onClick={onToggleDarkMode}
          title={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {isDarkMode ? <Sun size={18} className="theme-icon-svg" /> : <Moon size={18} className="theme-icon-svg" />}
          <span className="theme-label">{isDarkMode ? 'Light' : 'Dark'}</span>
        </button>

        <div className="user-section-container">
          <div
            ref={userSectionRef}
            className={`user-section ${showUserMenu ? 'active' : ''}`}
            onClick={() => setShowUserMenu(!showUserMenu)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                setShowUserMenu(!showUserMenu);
              }
            }}
            aria-expanded={showUserMenu}
            aria-haspopup="true"
          >
            <div className="user-info">
              <div className="user-avatar">{username.charAt(0).toUpperCase()}</div>
              <div className="user-details">
                <span className="user-name">{username}</span>
              </div>
            </div>
            <ChevronUp
              size={18}
              className={`user-menu-chevron ${showUserMenu ? 'open' : ''}`}
            />
          </div>

          {showUserMenu && (
            <div ref={menuRef} className="user-dropdown-menu">
              <button
                className="user-dropdown-item"
                onClick={handleSettingsClick}
                aria-label="Open settings"
              >
                <SettingsIcon size={18} />
                <span>Settings</span>
              </button>
              <div className="user-dropdown-divider" />
              <button
                className="user-dropdown-item logout-item"
                onClick={handleLogoutClick}
                aria-label="Logout"
              >
                <LogOut size={18} />
                <span>Logout</span>
              </button>
            </div>
          )}
        </div>
      </div>

      <Settings
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
        username={username}
      />
    </div>
  );
}

export default Sidebar;
