import React from 'react';
import { C } from '../primitives/Colors';

interface GoldBtnProps {
  children: React.ReactNode;
  onClick?: () => void;
  full?: boolean;
  outline?: boolean;
  disabled?: boolean;
  style?: React.CSSProperties;
}

export const GoldBtn = ({
  children,
  onClick,
  full = false,
  outline = false,
  disabled = false,
  style,
}: GoldBtnProps) => (
  <button
    onClick={onClick}
    disabled={disabled}
    style={{
      background: outline
        ? 'transparent'
        : `linear-gradient(135deg, ${C.gold}, ${C.goldLight})`,
      color: outline ? C.gold : C.bg,
      padding: '12px 20px',
      borderRadius: 12,
      fontWeight: 700,
      border: outline ? `2px solid ${C.gold}` : 'none',
      cursor: disabled ? 'not-allowed' : 'pointer',
      width: full ? '100%' : 'auto',
      fontSize: 14,
      transition: 'transform 0.2s, box-shadow 0.2s',
      opacity: disabled ? 0.5 : 1,
      ...style,
    }}
  >
    {children}
  </button>
);

interface SubTabProps {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}

export const SubTab = ({ active, onClick, children }: SubTabProps) => (
  <button
    onClick={onClick}
    style={{
      padding: '8px 12px',
      borderRadius: 8,
      fontSize: 13,
      fontWeight: 600,
      border: 'none',
      cursor: 'pointer',
      backgroundColor: active ? C.gold : 'transparent',
      color: active ? C.bg : C.gray,
      transition: 'all 0.2s',
      whiteSpace: 'nowrap',
    }}
  >
    {children}
  </button>
);
