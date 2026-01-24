import React, { useMemo } from 'react';
import { C } from '../primitives/Colors';

interface CandlestickChartProps {
  symbol: string;
  isUp?: boolean;
}

interface Candle {
  o: number;
  c: number;
  h: number;
  l: number;
  v: number;
}

export const CandlestickChart = ({ symbol, isUp = true }: CandlestickChartProps) => {
  const candles = useMemo(() => {
    const data: Candle[] = [];
    let price = 100;
    for (let i = 0; i < 30; i++) {
      const direction = Math.random() > (isUp ? 0.45 : 0.55) ? 1 : -1;
      const move = Math.random() * 4 + 1;
      const open = price;
      const close = price + direction * move;
      const high = Math.max(open, close) + Math.random() * 2;
      const low = Math.min(open, close) - Math.random() * 2;
      const vol = 40 + Math.random() * 50;
      data.push({ o: open, c: close, h: high, l: low, v: vol });
      price = close;
    }
    return data;
  }, [symbol, isUp]);

  const minP = Math.min(...candles.map((c) => c.l)) - 2;
  const maxP = Math.max(...candles.map((c) => c.h)) + 2;
  const range = maxP - minP;
  const maxV = Math.max(...candles.map((c) => c.v));

  const w = 300;
  const h = 180;
  const chartH = 130;
  const volH = 40;
  const toY = (p: number) => 10 + ((maxP - p) / range) * (chartH - 20);
  const cw = 7;

  return (
    <div
      style={{
        height: 200,
        backgroundColor: C.bg,
        borderRadius: 12,
        padding: 10,
      }}
    >
      <svg
        width="100%"
        height="100%"
        viewBox={`0 0 ${w} ${h}`}
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          <linearGradient id="volUp" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#00C805" stopOpacity="0.5" />
            <stop offset="100%" stopColor="#00C805" stopOpacity="0.1" />
          </linearGradient>
          <linearGradient id="volDn" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#FF5000" stopOpacity="0.5" />
            <stop offset="100%" stopColor="#FF5000" stopOpacity="0.1" />
          </linearGradient>
        </defs>

        {/* Grid */}
        {[0.25, 0.5, 0.75].map((p, i) => (
          <line
            key={i}
            x1="5"
            y1={10 + p * (chartH - 20)}
            x2="295"
            y2={10 + p * (chartH - 20)}
            stroke="#1a2535"
            strokeWidth="0.5"
          />
        ))}

        {/* Candlesticks */}
        {candles.map((c, i) => {
          const x = 10 + i * 9.5;
          const up = c.c >= c.o;
          const color = up ? '#00C805' : '#FF5000';
          const top = toY(Math.max(c.o, c.c));
          const bot = toY(Math.min(c.o, c.c));
          const bodyH = Math.max(2, bot - top);

          return (
            <g key={i}>
              <line
                x1={x + cw / 2}
                y1={toY(c.h)}
                x2={x + cw / 2}
                y2={toY(c.l)}
                stroke={color}
                strokeWidth="1"
              />
              <rect x={x} y={top} width={cw} height={bodyH} fill={color} rx="1" />
            </g>
          );
        })}

        {/* Volume separator */}
        <line
          x1="0"
          y1={chartH + 5}
          x2={w}
          y2={chartH + 5}
          stroke="#1a2535"
          strokeWidth="0.5"
        />

        {/* Volume bars */}
        {candles.map((c, i) => {
          const x = 10 + i * 9.5;
          const barH = (c.v / maxV) * (volH - 10);
          const up = c.c >= c.o;
          return (
            <rect
              key={`v${i}`}
              x={x}
              y={h - 5 - barH}
              width={cw}
              height={barH}
              fill={up ? 'url(#volUp)' : 'url(#volDn)'}
              rx="1"
            />
          );
        })}

        {/* Price labels */}
        <text x="295" y="18" fill="#64748b" fontSize="8" textAnchor="end">
          ${maxP.toFixed(0)}
        </text>
        <text x="295" y={chartH - 5} fill="#64748b" fontSize="8" textAnchor="end">
          ${minP.toFixed(0)}
        </text>
      </svg>
    </div>
  );
};
