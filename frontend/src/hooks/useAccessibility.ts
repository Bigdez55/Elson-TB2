import { useCallback, useState, useEffect } from 'react';

interface UseAccessibilityReturn {
  isDarkMode: boolean;
  prefersReducedMotion: boolean;
  announce: (message: string, assertive?: boolean) => void;
  getAriaLabel: (element: string) => string;
  announceMessage: (message: string, assertive?: boolean) => void;
  trapFocus: (container: HTMLElement) => () => void;
}

/**
 * Hook for accessibility utilities
 */
export const useAccessibility = (): UseAccessibilityReturn => {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    // Check dark mode preference
    const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
    setIsDarkMode(darkModeQuery.matches);
    const handleDarkModeChange = (e: MediaQueryListEvent) => setIsDarkMode(e.matches);
    darkModeQuery.addEventListener('change', handleDarkModeChange);

    // Check reduced motion preference
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(motionQuery.matches);
    const handleMotionChange = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches);
    motionQuery.addEventListener('change', handleMotionChange);

    return () => {
      darkModeQuery.removeEventListener('change', handleDarkModeChange);
      motionQuery.removeEventListener('change', handleMotionChange);
    };
  }, []);

  const getAriaLabel = useCallback((element: string): string => {
    return element;
  }, []);

  const announce = useCallback((message: string, assertive: boolean = true): void => {
    // Create an aria-live region to announce the message
    const regionId = assertive ? 'aria-live-assertive' : 'aria-live-polite';
    let liveRegion = document.getElementById(regionId);
    if (!liveRegion) {
      liveRegion = document.createElement('div');
      liveRegion.id = regionId;
      liveRegion.setAttribute('aria-live', assertive ? 'assertive' : 'polite');
      liveRegion.setAttribute('aria-atomic', 'true');
      liveRegion.className = 'sr-only';
      liveRegion.style.position = 'absolute';
      liveRegion.style.left = '-10000px';
      liveRegion.style.width = '1px';
      liveRegion.style.height = '1px';
      liveRegion.style.overflow = 'hidden';
      document.body.appendChild(liveRegion);
    }
    liveRegion.textContent = message;
  }, []);

  // Alias for announce
  const announceMessage = announce;

  const trapFocus = useCallback((container: HTMLElement): (() => void) => {
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstFocusable = focusableElements[0] as HTMLElement;
    const lastFocusable = focusableElements[focusableElements.length - 1] as HTMLElement;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstFocusable) {
          lastFocusable?.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === lastFocusable) {
          firstFocusable?.focus();
          e.preventDefault();
        }
      }
    };

    container.addEventListener('keydown', handleKeyDown);
    return () => container.removeEventListener('keydown', handleKeyDown);
  }, []);

  return {
    isDarkMode,
    prefersReducedMotion,
    announce,
    getAriaLabel,
    announceMessage,
    trapFocus,
  };
};

export default useAccessibility;
