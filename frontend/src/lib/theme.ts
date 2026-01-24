export const THEMES = ['majestic-purple', 'legacy-gold', 'aqua-blue', 'elson-dark'] as const;
export type ThemeName = typeof THEMES[number];

export const DEFAULT_THEME: ThemeName = 'elson-dark';
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
  'elson-dark': {
    name: 'elson-dark',
    displayName: 'Elson Dark',
    description: 'Mobile-first dark theme with gold accents',
    previewColors: ['#0a0e17', '#d4a84b', '#f0d78c'],
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
