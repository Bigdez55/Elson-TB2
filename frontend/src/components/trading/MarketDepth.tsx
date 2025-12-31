import React, { useMemo } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { formatCurrency } from '../../utils/formatters';

interface MarketDepthProps {
  data: {
    bids: [number, number][];
    asks: [number, number][];
  };
  height?: number;
}

export default function MarketDepth({ data, height = 300 }: MarketDepthProps) {
  const chartData = useMemo(() => {
    const bidTotals = data.bids.reduce((acc, [price, volume], index) => {
      const total = data.bids
        .slice(0, index + 1)
        .reduce((sum, [_, vol]) => sum + vol, 0);
      acc.push({ price, bidTotal: total, askTotal: 0 });
      return acc;
    }, [] as any[]);

    const askTotals = data.asks.reduce((acc, [price, volume], index) => {
      const total = data.asks
        .slice(0, index + 1)
        .reduce((sum, [_, vol]) => sum + vol, 0);
      acc.push({ price, bidTotal: 0, askTotal: total });
      return acc;
    }, [] as any[]);

    return [...bidTotals.reverse(), ...askTotals].sort((a, b) => a.price - b.price);
  }, [data]);

  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData}>
          <XAxis
            dataKey="price"
            tickFormatter={(value) => formatCurrency(value)}
            type="number"
            domain={['dataMin', 'dataMax']}
          />
          <YAxis />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                return (
                  <div className="bg-gray-900 p-2 rounded border border-gray-700">
                    <p>Price: {formatCurrency(payload[0].payload.price)}</p>
                    <p>Bid Total: {payload[0].value?.toFixed(4)}</p>
                    <p>Ask Total: {payload[1].value?.toFixed(4)}</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Area
            type="stepAfter"
            dataKey="bidTotal"
            stroke="#10B981"
            fill="#10B981"
            fillOpacity={0.2}
            isAnimationActive={false}
          />
          <Area
            type="stepAfter"
            dataKey="askTotal"
            stroke="#EF4444"
            fill="#EF4444"
            fillOpacity={0.2}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}