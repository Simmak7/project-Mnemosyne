import React from 'react';

/**
 * Welcome step (step 0) - Logo monogram, title, and subtitle.
 * Uses the gradient glow treatment matching the sidebar logo.
 */
function WelcomeStep({ step }) {
  return (
    <div className="onboarding-welcome">
      <div className="onboarding-welcome-logo">
        <div className="onboarding-logo-glow" />
        <span className="onboarding-logo-letter">M</span>
      </div>

      <h2 className="onboarding-welcome-title">{step.title}</h2>
      <p className="onboarding-welcome-subtitle">{step.subtitle}</p>

      <div className="onboarding-welcome-divider" />

      <p className="onboarding-welcome-desc">{step.description}</p>

      <div className="onboarding-welcome-hint">
        <span className="onboarding-hint-icon">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path
              d="M8 1L10 5.5L15 6.5L11.5 10L12.5 15L8 12.5L3.5 15L4.5 10L1 6.5L6 5.5L8 1Z"
              stroke="currentColor"
              strokeWidth="1.2"
              strokeLinejoin="round"
            />
          </svg>
        </span>
        Use arrow keys to navigate, or Esc to skip
      </div>
    </div>
  );
}

export default WelcomeStep;
