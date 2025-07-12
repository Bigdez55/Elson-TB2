import React from 'react';
import { formatCurrency } from '../../utils/formatters';

interface OrderBookProps {
  data: {
    bids: [number, number][];
    asks: [number, number][];
  };
  depth?: number;
}

export default function OrderBook({ data, depth = 10 }: OrderBookProps) {
  const maxVolume = Math.max(
    ...data.bids.map(([_, volume]) => volume),
    ...data.asks.map(([_, volume]) => volume)
  );

  return (
    <div className="h-full">
      <div className="mb-2 flex justify-between text-sm text-gray-400">
        <span>Price</span>
        <span>Size</span>
        <span>Total</span>
      </div>

      {/* Asks (Sell Orders) */}
      <div className="space-y-1">
        {data.asks.slice(0, depth).map(([price, volume], index) => {
          const total = data.asks
            .slice(0, index + 1)
            .reduce((sum, [_, vol]) => sum + vol, 0);
          const volumePercentage = (volume / maxVolume) * 100;

          return (
            <div key={price} className="relative">
              <div
                className="absolute inset-0 bg-red-500/10"
                style={{ width: `${volumePercentage}%` }}
              />
              <div className="relative flex justify-between text-sm">
                <span className="text-red-500">{formatCurrency(price)}</span>
                <span>{volume.toFixed(4)}</span>
                <span>{total.toFixed(4)}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Spread */}
      <div className="my-2 flex justify-between text-sm text-gray-400">
        <span>Spread:</span>
        <span>{formatCurrency(data.asks[0][0] - data.bids[0][0])}</span>
        <span>
          {((data.asks[0][0] - data.bids[0][0]) / data.asks[0][0] * 100).toFixed(2)}%
        </span>
      </div>

      {/* Bids (Buy Orders) */}
      <div className="space-y-1">
        {data.bids.slice(0, depth).map(([price, volume], index) => {
          const total = data.bids
            .slice(0, index + 1)
            .reduce((sum, [_, vol]) => sum + vol, 0);
          const volumePercentage = (volume / maxVolume) * 100;

          return (
            <div key={price} className="relative">
              <div
                className="absolute inset-0 bg-green-500/10"
                style={{ width: `${volumePercentage}%` }}
              />
              <div className="relative flex justify-between text-sm">
                <span className="text-green-500">{formatCurrency(price)}</span>
                <span>{volume.toFixed(4)}</span>
                <span>{total.toFixed(4)}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}