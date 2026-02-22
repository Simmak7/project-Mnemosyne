import { useState, useEffect, useCallback, useMemo } from 'react';
import { TOTAL_STEPS } from '../constants/onboardingSteps';

const STORAGE_KEY_PREFIX = 'onboarding_completed';

/**
 * useOnboarding - manages tutorial wizard state.
 *
 * Key is per-user so each new account sees the tutorial on first login.
 * Listens for 'replay-onboarding' custom event from Settings.
 */
export function useOnboarding() {
  const storageKey = useMemo(() => {
    const username = localStorage.getItem('username');
    return username ? `${STORAGE_KEY_PREFIX}_${username}` : STORAGE_KEY_PREFIX;
  }, []);

  const [completed, setCompletedState] = useState(() => {
    try {
      return localStorage.getItem(storageKey) === 'true';
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
        localStorage.setItem(storageKey, 'true');
      } else {
        localStorage.removeItem(storageKey);
      }
    } catch { /* ignore */ }
  }, [storageKey]);

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
