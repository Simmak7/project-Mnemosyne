import { useState, useEffect, useCallback } from 'react';
import { TOTAL_STEPS } from '../constants/onboardingSteps';

const STORAGE_KEY = 'onboarding_completed';

/**
 * useOnboarding - manages tutorial wizard state.
 *
 * Uses a non-prefixed localStorage key so it survives logout
 * (useAuth clears all `mnemosyne:*` keys on logout).
 * Listens for 'replay-onboarding' custom event from Settings.
 */
export function useOnboarding() {
  const [completed, setCompletedState] = useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) === 'true';
    } catch {
      return false;
    }
  });
  const [currentStep, setCurrentStep] = useState(0);
  const [direction, setDirection] = useState('forward');

  const setCompleted = useCallback((val) => {
    setCompletedState(val);
    try {
      if (val) {
        localStorage.setItem(STORAGE_KEY, 'true');
      } else {
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch { /* ignore */ }
  }, []);

  const isVisible = !completed;
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === TOTAL_STEPS - 1;

  const next = useCallback(() => {
    if (isLastStep) return;
    setDirection('forward');
    setCurrentStep(s => s + 1);
  }, [isLastStep]);

  const back = useCallback(() => {
    if (isFirstStep) return;
    setDirection('back');
    setCurrentStep(s => s - 1);
  }, [isFirstStep]);

  const complete = useCallback(() => {
    setCompleted(true);
  }, [setCompleted]);

  const skip = useCallback(() => {
    setCompleted(true);
  }, [setCompleted]);

  // Listen for replay event from Settings
  useEffect(() => {
    const handleReplay = () => {
      setCurrentStep(0);
      setDirection('forward');
      setCompleted(false);
    };
    window.addEventListener('replay-onboarding', handleReplay);
    return () => window.removeEventListener('replay-onboarding', handleReplay);
  }, [setCompleted]);

  // Lock body scroll while visible
  useEffect(() => {
    if (!isVisible) return;
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, [isVisible]);

  // Keyboard navigation
  useEffect(() => {
    if (!isVisible) return;
    const handleKey = (e) => {
      if (e.key === 'Escape') skip();
      else if (e.key === 'ArrowRight') next();
      else if (e.key === 'ArrowLeft') back();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [isVisible, skip, next, back]);

  return {
    isVisible,
    currentStep,
    totalSteps: TOTAL_STEPS,
    direction,
    isFirstStep,
    isLastStep,
    next,
    back,
    skip,
    complete,
  };
}
