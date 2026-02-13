import React from 'react';

/**
 * Dot-based step indicator with active/completed states.
 * Shows "Step X of Y" label beneath the dots.
 */
function StepIndicator({ currentStep, totalSteps }) {
  return (
    <div className="onboarding-indicator">
      <div className="onboarding-dots">
        {Array.from({ length: totalSteps }, (_, i) => (
          <button
            key={i}
            className={`onboarding-dot ${
              i === currentStep ? 'active' : ''
            } ${i < currentStep ? 'completed' : ''}`}
            aria-label={`Go to step ${i + 1}`}
            tabIndex={-1}
          />
        ))}
      </div>
      <span className="onboarding-step-label">
        Step {currentStep + 1} of {totalSteps}
      </span>
    </div>
  );
}

export default StepIndicator;
