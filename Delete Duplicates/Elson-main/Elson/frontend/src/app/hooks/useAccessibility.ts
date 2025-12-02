import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface AccessibilityContextType {
  // Theme mode
  isDarkMode: boolean;
  toggleDarkMode: () => void;
  setDarkMode: (isDark: boolean) => void;
  
  // Text size
  textSize: 'default' | 'large' | 'larger';
  setTextSize: (size: 'default' | 'large' | 'larger') => void;
  
  // Reduced motion
  prefersReducedMotion: boolean;
  setPrefersReducedMotion: (reduced: boolean) => void;
  
  // High contrast
  isHighContrast: boolean;
  toggleHighContrast: () => void;
  
  // Focus outline
  focusOutlineVisible: boolean;
  setFocusOutlineVisible: (visible: boolean) => void;
  
  // Announcements for screen readers
  announce: (message: string, assertive?: boolean) => void;
}

const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined);

interface AccessibilityProviderProps {
  children: ReactNode;
}

export const AccessibilityProvider = ({ children }: AccessibilityProviderProps) => {
  // Initialize from localStorage or system preferences
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem('elson-dark-mode');
    if (saved !== null) {
      return saved === 'true';
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });
  
  const [textSize, setTextSize] = useState<'default' | 'large' | 'larger'>(() => {
    const saved = localStorage.getItem('elson-text-size');
    if (saved !== null && ['default', 'large', 'larger'].includes(saved)) {
      return saved as 'default' | 'large' | 'larger';
    }
    return 'default';
  });
  
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(() => {
    const saved = localStorage.getItem('elson-reduced-motion');
    if (saved !== null) {
      return saved === 'true';
    }
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  });
  
  const [isHighContrast, setIsHighContrast] = useState(() => {
    const saved = localStorage.getItem('elson-high-contrast');
    if (saved !== null) {
      return saved === 'true';
    }
    return window.matchMedia('(forced-colors: active)').matches;
  });
  
  const [focusOutlineVisible, setFocusOutlineVisible] = useState(true);
  
  // Toggle functions
  const toggleDarkMode = () => {
    setIsDarkMode(prev => !prev);
  };
  
  const toggleHighContrast = () => {
    setIsHighContrast(prev => !prev);
  };
  
  // Screen reader announcements
  const announce = (message: string, assertive = false) => {
    const announcer = document.getElementById(
      assertive ? 'assertive-announcer' : 'polite-announcer'
    );
    
    if (announcer) {
      announcer.textContent = '';
      // Trigger a browser reflow
      void announcer.offsetWidth;
      announcer.textContent = message;
    }
  };
  
  // Sync with localStorage
  useEffect(() => {
    localStorage.setItem('elson-dark-mode', isDarkMode.toString());
    document.documentElement.classList.toggle('dark', isDarkMode);
  }, [isDarkMode]);
  
  useEffect(() => {
    localStorage.setItem('elson-text-size', textSize);
    document.documentElement.classList.remove('text-size-default', 'text-size-large', 'text-size-larger');
    document.documentElement.classList.add(`text-size-${textSize}`);
  }, [textSize]);
  
  useEffect(() => {
    localStorage.setItem('elson-reduced-motion', prefersReducedMotion.toString());
    document.documentElement.classList.toggle('reduce-motion', prefersReducedMotion);
  }, [prefersReducedMotion]);
  
  useEffect(() => {
    localStorage.setItem('elson-high-contrast', isHighContrast.toString());
    document.documentElement.classList.toggle('high-contrast', isHighContrast);
  }, [isHighContrast]);
  
  // Watch for system preference changes
  useEffect(() => {
    const darkModeMedia = window.matchMedia('(prefers-color-scheme: dark)');
    const reducedMotionMedia = window.matchMedia('(prefers-reduced-motion: reduce)');
    const highContrastMedia = window.matchMedia('(forced-colors: active)');
    
    const darkModeHandler = (e: MediaQueryListEvent) => {
      // Only change if user hasn't explicitly set a preference
      if (localStorage.getItem('elson-dark-mode') === null) {
        setIsDarkMode(e.matches);
      }
    };
    
    const reducedMotionHandler = (e: MediaQueryListEvent) => {
      if (localStorage.getItem('elson-reduced-motion') === null) {
        setPrefersReducedMotion(e.matches);
      }
    };
    
    const highContrastHandler = (e: MediaQueryListEvent) => {
      if (localStorage.getItem('elson-high-contrast') === null) {
        setIsHighContrast(e.matches);
      }
    };
    
    // Add event listeners
    try {
      // Modern browsers
      darkModeMedia.addEventListener('change', darkModeHandler);
      reducedMotionMedia.addEventListener('change', reducedMotionHandler);
      highContrastMedia.addEventListener('change', highContrastHandler);
    } catch (e) {
      // Fallback for older browsers
      darkModeMedia.addListener(darkModeHandler);
      reducedMotionMedia.addListener(reducedMotionHandler);
      highContrastMedia.addListener(highContrastHandler);
    }
    
    // Create screen reader announcement elements
    if (!document.getElementById('assertive-announcer')) {
      const assertiveAnnouncer = document.createElement('div');
      assertiveAnnouncer.id = 'assertive-announcer';
      assertiveAnnouncer.setAttribute('aria-live', 'assertive');
      assertiveAnnouncer.setAttribute('aria-atomic', 'true');
      assertiveAnnouncer.className = 'sr-only';
      document.body.appendChild(assertiveAnnouncer);
    }
    
    if (!document.getElementById('polite-announcer')) {
      const politeAnnouncer = document.createElement('div');
      politeAnnouncer.id = 'polite-announcer';
      politeAnnouncer.setAttribute('aria-live', 'polite');
      politeAnnouncer.setAttribute('aria-atomic', 'true');
      politeAnnouncer.className = 'sr-only';
      document.body.appendChild(politeAnnouncer);
    }
    
    // Cleanup
    return () => {
      try {
        // Modern browsers
        darkModeMedia.removeEventListener('change', darkModeHandler);
        reducedMotionMedia.removeEventListener('change', reducedMotionHandler);
        highContrastMedia.removeEventListener('change', highContrastHandler);
      } catch (e) {
        // Fallback for older browsers
        darkModeMedia.removeListener(darkModeHandler);
        reducedMotionMedia.removeListener(reducedMotionHandler);
        highContrastMedia.removeListener(highContrastHandler);
      }
      
      const assertiveAnnouncer = document.getElementById('assertive-announcer');
      const politeAnnouncer = document.getElementById('polite-announcer');
      
      if (assertiveAnnouncer) document.body.removeChild(assertiveAnnouncer);
      if (politeAnnouncer) document.body.removeChild(politeAnnouncer);
    };
  }, []);
  
  // Add keyboard listener for focus visibility
  useEffect(() => {
    const handleFirstTab = (e: KeyboardEvent) => {
      if (e.key === 'Tab') {
        document.body.classList.add('user-is-tabbing');
        setFocusOutlineVisible(true);
        window.removeEventListener('keydown', handleFirstTab);
        window.addEventListener('mousedown', handleMouseDown);
      }
    };
    
    const handleMouseDown = () => {
      document.body.classList.remove('user-is-tabbing');
      setFocusOutlineVisible(false);
      window.removeEventListener('mousedown', handleMouseDown);
      window.addEventListener('keydown', handleFirstTab);
    };
    
    window.addEventListener('keydown', handleFirstTab);
    
    return () => {
      window.removeEventListener('keydown', handleFirstTab);
      window.removeEventListener('mousedown', handleMouseDown);
    };
  }, []);
  
  const value: AccessibilityContextType = {
    isDarkMode,
    toggleDarkMode,
    setDarkMode: (isDark: boolean) => setIsDarkMode(isDark),
    
    textSize,
    setTextSize,
    
    prefersReducedMotion,
    setPrefersReducedMotion,
    
    isHighContrast,
    toggleHighContrast,
    
    focusOutlineVisible,
    setFocusOutlineVisible,
    
    announce,
  };
  
  return (
    <AccessibilityContext.Provider value={value}>
      {children}
    </AccessibilityContext.Provider>
  );
};

export const useAccessibility = (): AccessibilityContextType => {
  const context = useContext(AccessibilityContext);
  
  if (context === undefined) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider');
  }
  
  return context;
};