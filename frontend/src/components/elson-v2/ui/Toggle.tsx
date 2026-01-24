import React from 'react';
import { C } from '../primitives/Colors';

interface ToggleProps {
  on: boolean;
  onToggle?: () => void;
}

export const Toggle = ({ on, onToggle }: ToggleProps) => (
  <div
    onClick={onToggle}
    style={{
      width: 48,
      height: 26,
      borderRadius: 9999,
      backgroundColor: on ? C.gold : C.grayDark,
      position: 'relative',
      cursor: onToggle ? 'pointer' : 'default',
      transition: 'background 0.2s',
    }}
  >
    <div
      style={{
        width: 22,
        height: 22,
        borderRadius: 9999,
        backgroundColor: C.white,
        position: 'absolute',
        top: 2,
        left: on ? 24 : 2,
        transition: 'left 0.2s',
        boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
      }}
    />
  </div>
);
