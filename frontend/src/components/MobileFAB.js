import React, { useState, useCallback } from 'react';
import { Plus, FileText, Camera, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import './MobileFAB.css';

const FAB_ACTIONS = [
  { id: 'note', icon: FileText, label: 'New Note', tab: 'notes', color: '#fbbf24' },
  { id: 'photo', icon: Camera, label: 'Upload', tab: 'upload', color: '#22d3ee' },
];

const FAB_VISIBLE_TABS = ['dashboard', 'gallery'];

function MobileFAB({ onTabChange, isKeyboardOpen, activeTab }) {
  const [isOpen, setIsOpen] = useState(false);

  const triggerHaptic = useCallback(() => {
    if (navigator.vibrate) navigator.vibrate(10);
  }, []);

  const handleToggle = useCallback(() => {
    triggerHaptic();
    setIsOpen(prev => !prev);
  }, [triggerHaptic]);

  const handleAction = useCallback((action) => {
    triggerHaptic();
    setIsOpen(false);
    onTabChange(action.tab);
  }, [onTabChange, triggerHaptic]);

  if (!FAB_VISIBLE_TABS.includes(activeTab)) return null;

  return (
    <div className={`mobile-fab-container${isKeyboardOpen ? ' keyboard-open' : ''}`}>
      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div
              className="fab-backdrop"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
              onClick={() => setIsOpen(false)}
            />
            {FAB_ACTIONS.map((action, i) => {
              const Icon = action.icon;
              return (
                <motion.button
                  key={action.id}
                  className="fab-action"
                  initial={{ opacity: 0, y: 20, scale: 0.8 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 10, scale: 0.8 }}
                  transition={{ delay: i * 0.05, duration: 0.15 }}
                  onClick={() => handleAction(action)}
                  aria-label={action.label}
                >
                  <span className="fab-action-label">{action.label}</span>
                  <span
                    className="fab-action-icon"
                    style={{ background: action.color }}
                  >
                    <Icon size={18} />
                  </span>
                </motion.button>
              );
            })}
          </>
        )}
      </AnimatePresence>

      <motion.button
        className="fab-main"
        onClick={handleToggle}
        animate={{ rotate: isOpen ? 45 : 0 }}
        transition={{ duration: 0.2 }}
        aria-label={isOpen ? 'Close menu' : 'Quick actions'}
        aria-expanded={isOpen}
      >
        {isOpen ? <X size={24} /> : <Plus size={24} />}
      </motion.button>
    </div>
  );
}

export default MobileFAB;
