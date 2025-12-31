import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import {
  ThemeName,
  THEMES,
  DEFAULT_THEME,
  getStoredTheme,
  setStoredTheme
} from '../lib/theme';

interface ThemeContextValue {
  theme: ThemeName;
  setTheme: (theme: ThemeName) => void;
  cycleTheme: () => void;
  availableThemes: readonly ThemeName[];
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

interface ThemeProviderProps {
  children: React.ReactNode;
  defaultTheme?: ThemeName;
}

export function ThemeProvider({ children, defaultTheme }: ThemeProviderProps) {
  const [theme, setThemeState] = useState<ThemeName>(defaultTheme ?? DEFAULT_THEME);
  const [mounted, setMounted] = useState(false);

  // Initialize theme from localStorage on mount
  useEffect(() => {
    const storedTheme = getStoredTheme();
    setThemeState(storedTheme);
    document.documentElement.setAttribute('data-theme', storedTheme);
    setMounted(true);
  }, []);

  // Update DOM and localStorage when theme changes
  const setTheme = useCallback((newTheme: ThemeName) => {
    setThemeState(newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
    setStoredTheme(newTheme);

    // Dispatch custom event for components that need to react
    window.dispatchEvent(new CustomEvent('themechange', {
      detail: { theme: newTheme }
    }));
  }, []);

  // Cycle through themes
  const cycleTheme = useCallback(() => {
    const currentIndex = THEMES.indexOf(theme);
    const nextIndex = (currentIndex + 1) % THEMES.length;
    setTheme(THEMES[nextIndex]);
  }, [theme, setTheme]);

  // Prevent flash of incorrect theme
  if (!mounted) {
    return null;
  }

  return (
    <ThemeContext.Provider
      value={{
        theme,
        setTheme,
        cycleTheme,
        availableThemes: THEMES
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

// Hook for listening to theme changes (useful for animations, charts, etc.)
export function useThemeChange(callback: (theme: ThemeName) => void) {
  useEffect(() => {
    const handler = (e: CustomEvent<{ theme: ThemeName }>) => {
      callback(e.detail.theme);
    };

    window.addEventListener('themechange', handler as EventListener);
    return () => window.removeEventListener('themechange', handler as EventListener);
  }, [callback]);
}

export default ThemeContext;
