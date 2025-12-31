export const THEMES = ['majestic-purple', 'legacy-gold', 'aqua-blue'] as const;
export type ThemeName = typeof THEMES[number];

export const DEFAULT_THEME: ThemeName = 'majestic-purple';
export const THEME_STORAGE_KEY = 'elson-theme';

export interface ThemeConfig {
  name: ThemeName;
  displayName: string;
  description: string;
  previewColors: [string, string, string]; // For theme selector preview
}

export const themeConfigs: Record<ThemeName, ThemeConfig> = {
  'majestic-purple': {
    name: 'majestic-purple',
    displayName: 'Majestic Purple',
    description: 'Classic elegance with rich purple gradients',
    previewColors: ['#0f0c29', '#7e22ce', '#a855f7'],
  },
  'legacy-gold': {
    name: 'legacy-gold',
    displayName: 'Legacy Gold',
    description: 'Premium sophistication with gold accents',
    previewColors: ['#0f0c29', '#D4AF37', '#F9D65C'],
  },
  'aqua-blue': {
    name: 'aqua-blue',
    displayName: 'Aqua Blue',
    description: 'Fluid design evoking liquidity and flow',
    previewColors: ['#0a1628', '#1a2980', '#26d0ce'],
  },
};

export function isValidTheme(theme: string): theme is ThemeName {
  return THEMES.includes(theme as ThemeName);
}

export function getStoredTheme(): ThemeName {
  if (typeof window === 'undefined') return DEFAULT_THEME;
  const stored = localStorage.getItem(THEME_STORAGE_KEY);
  return stored && isValidTheme(stored) ? stored : DEFAULT_THEME;
}

export function setStoredTheme(theme: ThemeName): void {
  localStorage.setItem(THEME_STORAGE_KEY, theme);
}
