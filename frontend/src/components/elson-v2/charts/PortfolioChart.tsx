import React, { useMemo } from 'react';
import { C } from '../primitives/Colors';

interface PortfolioChartProps {
  timeRange: string;
  startValue?: number;
  endValue?: number;
}

export const PortfolioChart = ({
  timeRange,
  startValue = 35000,
  endValue = 42054.95,
}: PortfolioChartProps) => {
  const dataPoints = useMemo(() => {
    const counts: Record<string, number> = {
      '1D': 24,
      '1W': 7,
      '1M': 30,
      '3M': 12,
      '1Y': 12,
      ALL: 24,
    };
    const count = counts[timeRange] || 12;
    const points: number[] = [];
    const value = startValue;
    const trend = (endValue - value) / count;

    for (let i = 0; i <= count; i++) {
      const noise = (Math.random() - 0.45) * 1200;
      const progress = i / count;
      const targetValue = value + trend * i + noise;
      points.push(
        Math.max(
          startValue - 2000,
          Math.min(endValue + 2000, targetValue + progress * 2000)
        )
      );
    }
    points[points.length - 1] = endValue;
    return points;
  }, [timeRange, startValue, endValue]);

  const minVal = Math.min(...dataPoints) - 500;
  const maxVal = Math.max(...dataPoints) + 500;
  const range = maxVal - minVal;

  const width = 300;
  const height = 120;
  const padding = { top: 10, bottom: 25, left: 5, right: 5 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const xScale = (i: number) =>
    padding.left + (i / (dataPoints.length - 1)) * chartW;
  const yScale = (v: number) =>
    padding.top + ((maxVal - v) / range) * chartH;

  const linePath = dataPoints
    .map((v, i) => `${i === 0 ? 'M' : 'L'} ${xScale(i)} ${yScale(v)}`)
    .join(' ');
  const areaPath =
    linePath +
    ` L ${xScale(dataPoints.length - 1)} ${height - padding.bottom} L ${xScale(0)} ${height - padding.bottom} Z`;

  const isPositive = dataPoints[dataPoints.length - 1] >= dataPoints[0];
  const lineColor = isPositive ? '#00C805' : '#FF5000';

  const timeLabels: Record<string, { start: string; end: string }> = {
    '1D': { start: '9:30 AM', end: '4:00 PM' },
    '1W': { start: 'Mon', end: 'Today' },
    '1M': { start: '1', end: '30' },
    '1Y': { start: 'Jan', end: 'Dec' },
    ALL: { start: 'Start', end: 'Now' },
  };
  const labels = timeLabels[timeRange] || timeLabels.ALL;

  return (
    <div
      style={{
        height: 140,
        position: 'relative',
        backgroundColor: C.bg,
        borderRadius: 12,
        marginTop: 8,
      }}
    >
      <svg
        width="100%"
        height="100%"
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={lineColor} stopOpacity="0.25" />
            <stop offset="100%" stopColor={lineColor} stopOpacity="0.02" />
          </linearGradient>
        </defs>

        {/* Grid lines */}
        {[0.25, 0.5, 0.75].map((pct, i) => (
          <line
            key={i}
            x1={padding.left}
            y1={padding.top + pct * chartH}
            x2={width - padding.right}
            y2={padding.top + pct * chartH}
            stroke="#1a2535"
            strokeWidth="0.5"
            strokeDasharray="4,4"
          />
        ))}

        {/* Area fill */}
        <path d={areaPath} fill="url(#areaGrad)" />

        {/* Main line */}
        <path
          d={linePath}
          fill="none"
          stroke={lineColor}
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* End point */}
        <circle
          cx={xScale(dataPoints.length - 1)}
          cy={yScale(dataPoints[dataPoints.length - 1])}
          r="4"
          fill={lineColor}
        />
        <circle
          cx={xScale(dataPoints.length - 1)}
          cy={yScale(dataPoints[dataPoints.length - 1])}
          r="7"
          fill={lineColor}
          opacity="0.3"
        />

        {/* Time labels */}
        <text
          x={padding.left + 5}
          y={height - 6}
          fill="#64748b"
          fontSize="9"
          fontFamily="system-ui"
        >
          {labels.start}
        </text>
        <text
          x={width - padding.right - 5}
          y={height - 6}
          fill="#64748b"
          fontSize="9"
          fontFamily="system-ui"
          textAnchor="end"
        >
          {labels.end}
        </text>
      </svg>
    </div>
  );
};
