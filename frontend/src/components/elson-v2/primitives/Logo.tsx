import React from 'react';
import { C } from './Colors';

interface LogoProps {
  size?: number;
}

export const Logo = ({ size = 32 }: LogoProps) => (
  <svg style={{ width: size, height: size }} viewBox="0 0 40 40" fill="none">
    <circle cx="20" cy="20" r="20" fill="url(#lg)" />
    <path d="M20 8L12 14V26L20 32L28 26V14L20 8Z" stroke={C.bg} strokeWidth="2" fill="none" />
    <path d="M20 12L15 16V24L20 28L25 24V16L20 12Z" fill={C.bg} />
    <defs>
      <linearGradient id="lg" x1="0" y1="0" x2="40" y2="40">
        <stop offset="0%" stopColor={C.gold} />
        <stop offset="100%" stopColor={C.goldLight} />
      </linearGradient>
    </defs>
  </svg>
);
