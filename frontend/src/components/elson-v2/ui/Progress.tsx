import React from 'react';
import { C } from '../primitives/Colors';

interface ProgressProps {
  value: number;
  max: number;
  color?: string;
}

export const Progress = ({ value, max, color = C.gold }: ProgressProps) => (
  <div
    style={{
      height: 6,
      borderRadius: 9999,
      backgroundColor: C.inner,
      overflow: 'hidden',
    }}
  >
    <div
      style={{
        height: '100%',
        borderRadius: 9999,
        background: `linear-gradient(90deg, ${color}, ${color}dd)`,
        width: `${Math.min((value / max) * 100, 100)}%`,
        transition: 'width 0.3s ease',
      }}
    />
  </div>
);

interface CircularProgressProps {
  value: number;
  max?: number;
  size?: number;
  strokeWidth?: number;
  color?: string;
}

export const CircularProgress = ({
  value,
  max = 100,
  size = 80,
  strokeWidth = 8,
  color = C.gold,
}: CircularProgressProps) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (value / max) * circumference;

  return (
    <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke={C.inner}
        strokeWidth={strokeWidth}
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        style={{ transition: 'stroke-dashoffset 0.5s ease' }}
      />
    </svg>
  );
};
