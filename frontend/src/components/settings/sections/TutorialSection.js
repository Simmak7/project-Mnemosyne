/**
 * Tutorial settings section - replay onboarding
 */
import React from 'react';
import { GraduationCap } from 'lucide-react';

function TutorialSection({ onClose }) {
  const handleReplay = () => {
    onClose();
    // Small delay so the settings modal closes first
    setTimeout(() => {
      window.dispatchEvent(new CustomEvent('replay-onboarding'));
    }, 200);
  };

  return (
    <div className="settings-section">
      <div className="settings-section-header">
        <GraduationCap size={20} />
        <h3>Tutorial</h3>
      </div>
      <div className="settings-item settings-item-action">
        <div className="settings-item-info">
          <label>App walkthrough</label>
          <p>Review the guided tour of all Mnemosyne features</p>
        </div>
        <button className="btn-secondary btn-small" onClick={handleReplay}>
          Replay Tutorial
        </button>
      </div>
    </div>
  );
}

export default TutorialSection;
