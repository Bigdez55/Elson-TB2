// Premium Dark Fintech Palette
export const C = {
  bg: '#0a0e17',
  card: '#0d1421',
  cardAlt: '#111927',
  inner: '#1a2332',
  border: '#1e293b',
  gold: '#d4a84b',
  goldLight: '#f0d78c',
  goldDark: '#b8860b',
  white: '#ffffff',
  gray: '#9ca3af',
  grayLight: '#d1d5db',
  grayDark: '#6b7280',
  green: '#10b981',
  greenLight: '#34d399',
  red: '#ef4444',
  yellow: '#f59e0b',
  blue: '#3b82f6',
  purple: '#8b5cf6',
} as const;

export type ColorKey = keyof typeof C;
