import React from 'react';
import { C } from '../primitives/Colors';

type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'gold' | 'purple';

interface BadgeProps {
  children: React.ReactNode;
  v?: BadgeVariant;
  style?: React.CSSProperties;
}

const colors: Record<BadgeVariant, { bg: string; text: string }> = {
  default: { bg: 'rgba(107,114,128,0.3)', text: C.gray },
  success: { bg: 'rgba(16,185,129,0.2)', text: C.green },
  warning: { bg: 'rgba(245,158,11,0.2)', text: C.yellow },
  danger: { bg: 'rgba(239,68,68,0.2)', text: C.red },
  gold: { bg: 'rgba(212,168,75,0.2)', text: C.gold },
  purple: { bg: 'rgba(139,92,246,0.2)', text: C.purple },
};

export const Badge = ({ children, v = 'default', style }: BadgeProps) => (
  <span
    style={{
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: colors[v].bg,
      color: colors[v].text,
      padding: '4px 10px',
      borderRadius: 6,
      fontSize: 10,
      fontWeight: 700,
      textTransform: 'uppercase',
      letterSpacing: 0.5,
      lineHeight: 1,
      whiteSpace: 'nowrap',
      flexShrink: 0,
      alignSelf: 'flex-start',
      height: 'fit-content',
      ...style,
    }}
  >
    {children}
  </span>
);
