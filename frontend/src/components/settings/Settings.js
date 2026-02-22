/**
 * Settings modal - main component
 * Composes all settings sections and modals
 */
import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';
import { useSettingsData } from './hooks/useSettingsData';

// Modals
import {
  ChangePasswordModal,
  TwoFactorSetupModal,
  EmailChangeModal
} from './modals';

// Sections
import {
  AccountSection,
  SecuritySection,
  AppearanceSection,
  AIModelsSection,
  CloudAISection,
  NotificationsSection,
  SessionsSection,
  DataSection,
  ExperimentalSection,
  TutorialSection
} from './sections';

// Import CSS from parent directory
import '../Settings.css';

function Settings({ isOpen, onClose, username, userEmail }) {
  // Modal visibility state
  const [showChangePassword, setShowChangePassword] = useState(false);
  const [showTwoFactorSetup, setShowTwoFactorSetup] = useState(false);
  const [showEmailChange, setShowEmailChange] = useState(false);

  // Use the settings data hook
  const {
    profile,
    twoFactorStatus,
    preferences,
    prefOptions,
    notifications,
    notifOptions,
    sessions,
    availableModels,
    modelConfig,
    featureFlags,
    setProfile,
    fetchProfile,
    fetch2FAStatus,
    toggleFeatureFlag,
    updatePreference,
    updateNotification,
    revokeSession,
    revokeAllSessions,
    refreshModels,
  } = useSettingsData(isOpen);

  if (!isOpen) return null;

  return createPortal(
    <div className="settings-overlay" onClick={onClose} role="presentation">
      <div
        className="settings-modal"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="settings-title"
      >
        <div className="settings-header">
          <h2 id="settings-title">Settings</h2>
          <button className="settings-close-btn" onClick={onClose} aria-label="Close settings">
            <X size={24} />
          </button>
        </div>

        <div className="settings-content">
          <AccountSection
            profile={profile}
            username={username}
            userEmail={userEmail}
            onEmailChangeClick={() => setShowEmailChange(true)}
            onProfileUpdate={setProfile}
          />

          <SecuritySection
            twoFactorStatus={twoFactorStatus}
            onChangePasswordClick={() => setShowChangePassword(true)}
            onTwoFactorSetupClick={() => setShowTwoFactorSetup(true)}
            onDisable2FA={fetch2FAStatus}
          />

          <AppearanceSection
            preferences={preferences}
            prefOptions={prefOptions}
            onPreferenceUpdate={updatePreference}
          />

          <AIModelsSection
            availableModels={availableModels}
            modelConfig={modelConfig}
            preferences={preferences}
            onPreferenceUpdate={updatePreference}
            onModelsChanged={refreshModels}
          />

          <CloudAISection
            preferences={preferences}
            availableModels={availableModels}
            onPreferenceUpdate={updatePreference}
          />

          <NotificationsSection />

          <SessionsSection
            sessions={sessions}
            onRevokeSession={revokeSession}
            onRevokeAllSessions={revokeAllSessions}
          />

          <DataSection />

          <TutorialSection onClose={onClose} />

          <ExperimentalSection
            featureFlags={featureFlags}
            onToggleFlag={toggleFeatureFlag}
          />
        </div>

        <div className="settings-footer">
          <p className="settings-version">Mnemosyne v1.1.0</p>
        </div>
      </div>

      <ChangePasswordModal
        isOpen={showChangePassword}
        onClose={() => setShowChangePassword(false)}
      />

      <TwoFactorSetupModal
        isOpen={showTwoFactorSetup}
        onClose={() => setShowTwoFactorSetup(false)}
        onComplete={fetch2FAStatus}
      />

      <EmailChangeModal
        isOpen={showEmailChange}
        onClose={() => setShowEmailChange(false)}
        currentEmail={profile?.email || userEmail}
        onSuccess={fetchProfile}
      />
    </div>,
    document.body
  );
}

export default Settings;
