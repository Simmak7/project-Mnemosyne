import React from 'react';
import { CheckCircle } from 'lucide-react';

/**
 * Completion step (step 10) - Checkmark, congratulations, CTA.
 * Uses gradient glow similar to the welcome step.
 */
function CompletionStep({ step, onComplete }) {
  return (
    <div className="onboarding-completion">
      <div className="onboarding-completion-icon">
        <div className="onboarding-completion-glow" />
        <CheckCircle size={48} strokeWidth={1.5} />
      </div>

      <h2 className="onboarding-completion-title">{step.title}</h2>
      <p className="onboarding-completion-desc">{step.description}</p>

      <button
        className="onboarding-btn onboarding-btn-primary onboarding-btn-cta"
        onClick={onComplete}
      >
        Get Started
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="onboarding-arrow">
          <path d="M3 8H13M13 8L9 4M13 8L9 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
    </div>
  );
}

export default CompletionStep;
