import React from 'react';
import { C } from '../primitives/Colors';

interface CardProps {
  children: React.ReactNode;
  style?: React.CSSProperties;
  onClick?: () => void;
}

export const Card = ({ children, style = {}, onClick }: CardProps) => (
  <div
    onClick={onClick}
    style={{
      backgroundColor: C.card,
      borderRadius: 16,
      padding: 16,
      border: `1px solid ${C.border}`,
      cursor: onClick ? 'pointer' : undefined,
      ...style,
    }}
  >
    {children}
  </div>
);

export const Inner = ({ children, style = {}, onClick }: CardProps) => (
  <div
    onClick={onClick}
    style={{
      backgroundColor: C.inner,
      borderRadius: 12,
      padding: 12,
      cursor: onClick ? 'pointer' : undefined,
      ...style,
    }}
  >
    {children}
  </div>
);
