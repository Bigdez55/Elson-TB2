import React, { useEffect, useState } from 'react';
import { useAppSelector } from '../../store/hooks';
import { selectMarketData, selectSymbolPrice } from '../../store/slices/websocketSlice';
import { useMarketDataWebSocket } from '../../hooks/useWebSocket';
import { CompactConnectionStatus } from '../common/ConnectionStatusBanner';
import { Badge } from '../common/Badge';

interface LiveMarketDataProps {
  symbol: string;
  onPriceUpdate?: (price: number, change: number, changePercent: number) => void;
  showConnectionStatus?: boolean;
  className?: string;
}

export const LiveMarketData: React.FC<LiveMarketDataProps> = ({
  symbol,
  onPriceUpdate,
  showConnectionStatus = true,
  className = '',
}) => {
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [priceDirection, setPriceDirection] = useState<'up' | 'down' | 'neutral'>('neutral');
  const [previousPrice, setPreviousPrice] = useState<number | null>(null);

  // Use specialized WebSocket hook for market data
  const { isConnected, marketData, error } = useMarketDataWebSocket([symbol]);
  
  // Get current symbol data
  const symbolData = marketData[symbol];
  const currentPrice = useAppSelector(selectSymbolPrice(symbol));

  // Handle price changes and animations
  useEffect(() => {
    if (symbolData && symbolData.price !== previousPrice) {
      if (previousPrice !== null) {
        setPriceDirection(symbolData.price > previousPrice ? 'up' : 'down');
        // Reset direction after animation
        setTimeout(() => setPriceDirection('neutral'), 1000);
      }
      setPreviousPrice(symbolData.price);
      setLastUpdate(new Date());
      
      // Notify parent component
      onPriceUpdate?.(
        symbolData.price,
        symbolData.change,
        symbolData.change_percent
      );
    }
  }, [symbolData, previousPrice, onPriceUpdate]);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price);
  };

  const formatChange = (change: number, changePercent: number) => {
    const sign = change > 0 ? '+' : '';
    const formattedChange = `${sign}${change.toFixed(2)}`;
    const formattedPercent = `${sign}${changePercent.toFixed(2)}%`;
    return `${formattedChange} (${formattedPercent})`;
  };

  const formatVolume = (volume: number) => {
    if (volume >= 1000000) {
      return `${(volume / 1000000).toFixed(1)}M`;
    } else if (volume >= 1000) {
      return `${(volume / 1000).toFixed(1)}K`;
    }
    return volume.toString();
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const getPriceColorClass = (change: number) => {
    if (change > 0) return 'text-green-400';
    if (change < 0) return 'text-red-400';
    return 'text-gray-300';
  };

  const getPriceAnimationClass = () => {
    switch (priceDirection) {
      case 'up': return 'animate-pulse bg-green-900 bg-opacity-30';
      case 'down': return 'animate-pulse bg-red-900 bg-opacity-30';
      default: return '';
    }
  };

  if (!symbolData && !isConnected) {
    return (
      <div className={`bg-gray-800 rounded-lg p-4 ${className}`}>
        <div className="flex items-center justify-between">
          <div className="text-gray-400">
            <div className="text-lg font-bold">{symbol}</div>
            <div className="text-sm">Market Data Unavailable</div>
          </div>
          {showConnectionStatus && <CompactConnectionStatus />}
        </div>
        {error && (
          <div className="mt-2 text-red-400 text-xs">
            Error: {error}
          </div>
        )}
      </div>
    );
  }

  if (!symbolData) {
    return (
      <div className={`bg-gray-800 rounded-lg p-4 ${className}`}>
        <div className="flex items-center justify-between">
          <div className="text-gray-400">
            <div className="text-lg font-bold">{symbol}</div>
            <div className="text-sm">Loading market data...</div>
          </div>
          {showConnectionStatus && <CompactConnectionStatus />}
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-gray-800 rounded-lg p-4 transition-all duration-300 ${getPriceAnimationClass()} ${className}`}>
      {/* Header with connection status */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <h3 className="text-lg font-bold text-white">{symbol}</h3>
          {isConnected && (
            <Badge variant="success" size="sm">Live</Badge>
          )}
        </div>
        {showConnectionStatus && <CompactConnectionStatus />}
      </div>

      {/* Price Information */}
      <div className="grid grid-cols-2 gap-4">
        {/* Current Price */}
        <div>
          <div className="text-gray-400 text-sm">Current Price</div>
          <div className={`text-2xl font-bold transition-colors duration-300 ${getPriceColorClass(symbolData.change)}`}>
            {formatPrice(symbolData.price)}
          </div>
        </div>

        {/* Change */}
        <div>
          <div className="text-gray-400 text-sm">Change</div>
          <div className={`text-lg font-medium ${getPriceColorClass(symbolData.change)}`}>
            {formatChange(symbolData.change, symbolData.change_percent)}
          </div>
        </div>

        {/* Volume */}
        <div>
          <div className="text-gray-400 text-sm">Volume</div>
          <div className="text-white text-lg font-medium">
            {formatVolume(symbolData.volume)}
          </div>
        </div>

        {/* Last Update */}
        <div>
          <div className="text-gray-400 text-sm">Last Update</div>
          <div className="text-white text-sm">
            {formatTimestamp(symbolData.timestamp)}
          </div>
        </div>
      </div>

      {/* Bid/Ask if available */}
      {(symbolData.bid || symbolData.ask) && (
        <div className="mt-3 pt-3 border-t border-gray-700">
          <div className="grid grid-cols-2 gap-4 text-sm">
            {symbolData.bid && (
              <div>
                <span className="text-gray-400">Bid: </span>
                <span className="text-blue-400 font-medium">{formatPrice(symbolData.bid)}</span>
              </div>
            )}
            {symbolData.ask && (
              <div>
                <span className="text-gray-400">Ask: </span>
                <span className="text-red-400 font-medium">{formatPrice(symbolData.ask)}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Data freshness indicator */}
      {lastUpdate && (
        <div className="mt-2 text-xs text-gray-500">
          Last updated: {lastUpdate.toLocaleTimeString()}
        </div>
      )}
    </div>
  );
};

// Mini version for compact display
interface MiniLiveMarketDataProps {
  symbol: string;
  showChange?: boolean;
  className?: string;
}

export const MiniLiveMarketData: React.FC<MiniLiveMarketDataProps> = ({
  symbol,
  showChange = true,
  className = '',
}) => {
  const symbolData = useAppSelector((state) => state.websocket.marketData[symbol]);
  const isConnected = useAppSelector((state) => state.websocket.status === 'AUTHENTICATED');

  if (!symbolData) {
    return (
      <div className={`inline-flex items-center space-x-2 ${className}`}>
        <span className="text-gray-400 text-sm">{symbol}</span>
        <span className="text-gray-500 text-xs">--</span>
      </div>
    );
  }

  const getPriceColor = (change: number) => {
    if (change > 0) return 'text-green-400';
    if (change < 0) return 'text-red-400';
    return 'text-gray-300';
  };

  return (
    <div className={`inline-flex items-center space-x-2 ${className}`}>
      <span className="text-gray-400 text-sm font-medium">{symbol}</span>
      <span className={`text-sm font-bold ${getPriceColor(symbolData.change)}`}>
        ${symbolData.price.toFixed(2)}
      </span>
      {showChange && (
        <span className={`text-xs ${getPriceColor(symbolData.change)}`}>
          ({symbolData.change >= 0 ? '+' : ''}{symbolData.change_percent.toFixed(2)}%)
        </span>
      )}
      {isConnected && (
        <div className="h-2 w-2 bg-green-400 rounded-full animate-pulse" />
      )}
    </div>
  );
};

export default LiveMarketData;