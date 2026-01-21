import React from 'react';

interface PortfolioChartProps {
  className?: string;
}

export const PortfolioChart: React.FC<PortfolioChartProps> = ({ className = '' }) => (
  <div className={`h-[200px] lg:h-[240px] relative overflow-hidden ${className}`}>
    <svg width="100%" height="100%" viewBox="0 0 800 240" preserveAspectRatio="none">
      <defs>
        <linearGradient id="goldGradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="rgba(201, 162, 39, 0.3)"/>
          <stop offset="100%" stopColor="rgba(201, 162, 39, 0)"/>
        </linearGradient>
      </defs>
      <g stroke="rgba(255,255,255,0.05)" strokeWidth="1">
        <line x1="0" y1="60" x2="800" y2="60"/>
        <line x1="0" y1="120" x2="800" y2="120"/>
        <line x1="0" y1="180" x2="800" y2="180"/>
      </g>
      <path fill="url(#goldGradient)" d="M0,180 Q100,160 200,130 T400,100 T600,70 T800,80 L800,240 L0,240 Z"/>
      <path fill="none" stroke="#C9A227" strokeWidth="2" d="M0,180 Q100,160 200,130 T400,100 T600,70 T800,80"/>
      <circle cx="200" cy="130" r="4" fill="#C9A227"/>
      <circle cx="400" cy="100" r="4" fill="#C9A227"/>
      <circle cx="600" cy="70" r="4" fill="#C9A227"/>
      <circle cx="800" cy="80" r="4" fill="#C9A227"/>
    </svg>
  </div>
);

export default PortfolioChart;
