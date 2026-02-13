import React from 'react';
import { createPortal } from 'react-dom';
import { ONBOARDING_STEPS } from '../constants/onboardingSteps';
import { useOnboarding } from '../hooks/useOnboarding';
import WelcomeStep from './WelcomeStep';
import FeatureStep from './FeatureStep';
import CompletionStep from './CompletionStep';
import StepIndicator from './StepIndicator';
import './OnboardingModal.css';

/**
 * Root onboarding modal rendered via portal.
 * Renders nothing when the tutorial has been completed/skipped.
 */
function OnboardingModal() {
  const {
    isVisible,
    currentStep,
    totalSteps,
    direction,
    isFirstStep,
    isLastStep,
    next,
    back,
    skip,
    complete,
  } = useOnboarding();

  if (!isVisible) return null;

  const stepData = ONBOARDING_STEPS[currentStep];
  const animClass = direction === 'forward' ? 'slide-forward' : 'slide-back';

  const renderStep = () => {
    switch (stepData.type) {
      case 'welcome':
        return <WelcomeStep step={stepData} />;
      case 'completion':
        return <CompletionStep step={stepData} onComplete={complete} />;
      case 'feature':
      default:
        return <FeatureStep step={stepData} />;
    }
  };

  return createPortal(
    <div className="onboarding-overlay" role="dialog" aria-modal="true" aria-label="Onboarding tutorial">
      <div className="onboarding-modal">
        {/* Header - skip button */}
        <div className="onboarding-header">
          <button className="onboarding-skip" onClick={skip}>
            Skip Tutorial
          </button>
        </div>

        {/* Animated content area */}
        <div className="onboarding-content">
          <div key={currentStep} className={`onboarding-step-wrapper ${animClass}`}>
            {renderStep()}
          </div>
        </div>

        {/* Footer - indicator + nav */}
        {stepData.type !== 'completion' && (
          <div className="onboarding-footer">
            <div className="onboarding-nav">
              {!isFirstStep && (
                <button className="onboarding-btn onboarding-btn-secondary" onClick={back}>
                  Back
                </button>
              )}
            </div>

            <StepIndicator currentStep={currentStep} totalSteps={totalSteps} />

            <div className="onboarding-nav">
              {!isLastStep && (
                <button className="onboarding-btn onboarding-btn-primary" onClick={next}>
                  Next
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>,
    document.body
  );
}

export default OnboardingModal;
