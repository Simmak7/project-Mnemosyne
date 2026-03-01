import React, { useEffect } from 'react';
import {
  Upload, FileScan, BookOpen, Search, Settings as SettingsIcon,
  Sun, Moon, LogOut, X
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSidebarConfig } from '../hooks/useSidebarConfig';
import './MobileNavDrawer.css';

const DRAWER_ITEMS = [
  { id: 'upload', icon: Upload, label: 'Upload' },
  { id: 'documents', icon: FileScan, label: 'Documents', flag: 'ENABLE_DOCUMENTS' },
  { id: 'journal', icon: BookOpen, label: 'Journal', flag: 'ENABLE_JOURNAL' },
];

function MobileNavDrawer({
  isOpen,
  onClose,
  activeTab,
  onTabChange,
  username,
  onLogout,
  isDarkMode,
  onToggleDarkMode,
  onOpenSearch,
  onOpenSettings,
}) {
  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    const handleEsc = (e) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleEsc);
    return () => document.removeEventListener('keydown', handleEsc);
  }, [isOpen, onClose]);

  const { isTabVisible } = useSidebarConfig();

  // Filter items by feature flags and sidebar config
  const visibleItems = DRAWER_ITEMS.filter((item) => {
    if (!item.flag && !isTabVisible(item.id)) return false;
    if (item.flag && localStorage.getItem(item.flag) === 'false') return false;
    return isTabVisible(item.id);
  });

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            className="mobile-drawer-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
          />

          {/* Drawer */}
          <motion.div
            className="mobile-nav-drawer"
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
          >
            {/* Handle bar */}
            <div className="drawer-handle-bar">
              <div className="drawer-handle" />
            </div>

            {/* Close button */}
            <button className="drawer-close-btn" onClick={onClose} aria-label="Close menu">
              <X size={20} />
            </button>

            {/* Navigation items */}
            <div className="drawer-nav-section">
              {visibleItems.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.id}
                    className={`drawer-nav-item ${activeTab === item.id ? 'active' : ''}`}
                    onClick={() => onTabChange(item.id)}
                  >
                    <Icon size={20} />
                    <span>{item.label}</span>
                  </button>
                );
              })}

              {/* Search */}
              <button className="drawer-nav-item" onClick={onOpenSearch}>
                <Search size={20} />
                <span>Search</span>
              </button>
            </div>

            {/* Divider */}
            <div className="drawer-divider" />

            {/* Settings row */}
            <div className="drawer-actions-section">
              {onOpenSettings && (
                <button className="drawer-nav-item" onClick={onOpenSettings}>
                  <SettingsIcon size={20} />
                  <span>Settings</span>
                </button>
              )}
              <button className="drawer-nav-item" onClick={onToggleDarkMode}>
                {isDarkMode ? <Sun size={20} /> : <Moon size={20} />}
                <span>{isDarkMode ? 'Light Mode' : 'Dark Mode'}</span>
              </button>
            </div>

            {/* Divider */}
            <div className="drawer-divider" />

            {/* User section */}
            <div className="drawer-user-section">
              <div className="drawer-user-info">
                <div className="drawer-user-avatar">
                  {username?.charAt(0).toUpperCase()}
                </div>
                <span className="drawer-user-name">{username}</span>
              </div>
              <button className="drawer-logout-btn" onClick={onLogout}>
                <LogOut size={18} />
                <span>Logout</span>
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

export default MobileNavDrawer;
