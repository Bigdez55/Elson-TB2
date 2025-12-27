import React, { useEffect, useState } from 'react';
import { useAppSelector } from '../../store/hooks';
import { selectPortfolio, selectPositions, selectRecentOrders } from '../../store/slices/websocketSlice';
import { useTradingContext } from '../../contexts/TradingContext';
import { useTradingWebSocket } from '../../hooks/useWebSocket';
import { Badge } from '../common/Badge';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface LivePortfolioUpdatesProps {
  className?: string;
  showRecentOrders?: boolean;
  showPositions?: boolean;
  maxOrdersToShow?: number;
  maxPositionsToShow?: number;
}

export const LivePortfolioUpdates: React.FC<LivePortfolioUpdatesProps> = ({
  className = '',
  showRecentOrders = true,
  showPositions = true,
  maxOrdersToShow = 5,
  maxPositionsToShow = 5,
}) => {
  const { mode } = useTradingContext();
  const [lastPortfolioUpdate, setLastPortfolioUpdate] = useState<Date | null>(null);

  // Use specialized WebSocket hook for trading data
  const { isConnected, portfolio, positions, orders, error } = useTradingWebSocket(mode);

  // Also get data from Redux store
  const portfolioFromStore = useAppSelector(selectPortfolio(mode));
  const positionsFromStore = useAppSelector(selectPositions(mode));
  const ordersFromStore = useAppSelector(selectRecentOrders);

  // Use WebSocket data if available, fallback to store data
  const currentPortfolio = portfolio || portfolioFromStore;
  const currentPositions = Object.values(positions).length > 0 ? Object.values(positions) : positionsFromStore;
  const currentOrders = orders.length > 0 ? orders : ordersFromStore.filter(order => 
    order.paper_trading === (mode === 'paper')
  );

  useEffect(() => {
    if (currentPortfolio) {
      setLastPortfolioUpdate(new Date());
    }
  }, [currentPortfolio]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const getPnLColor = (value: number) => {
    if (value > 0) return 'text-green-400';
    if (value < 0) return 'text-red-400';
    return 'text-gray-300';
  };

  const getOrderStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'filled': return 'success';
      case 'partial_fill': return 'warning';
      case 'cancelled': return 'error';
      case 'pending': return 'info';
      default: return 'neutral';
    }
  };

  if (error) {
    return (
      <div className={`bg-gray-800 rounded-lg p-4 ${className}`}>
        <div className="text-red-400 text-center">
          <div className="text-sm font-medium mb-1">Real-time Updates Unavailable</div>
          <div className="text-xs">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Portfolio Summary */}
      <div className="bg-gray-800 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-medium text-white">Portfolio Summary</h3>
          <div className="flex items-center space-x-2">
            <Badge variant={mode === 'paper' ? 'warning' : 'info'} size="sm">
              {mode.toUpperCase()}
            </Badge>
            {isConnected && (
              <Badge variant="success" size="sm">Live</Badge>
            )}
          </div>
        </div>

        {currentPortfolio ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-gray-400 text-sm">Total Value</div>
              <div className="text-white text-xl font-bold">
                {formatCurrency(currentPortfolio.total_value)}
              </div>
            </div>
            
            <div>
              <div className="text-gray-400 text-sm">Cash Balance</div>
              <div className="text-white text-lg font-medium">
                {formatCurrency(currentPortfolio.cash_balance)}
              </div>
            </div>
            
            <div>
              <div className="text-gray-400 text-sm">Day P&L</div>
              <div className={`text-lg font-medium ${getPnLColor(currentPortfolio.day_pnl)}`}>
                {formatCurrency(currentPortfolio.day_pnl)}
              </div>
            </div>
            
            <div>
              <div className="text-gray-400 text-sm">Day P&L %</div>
              <div className={`text-lg font-medium ${getPnLColor(currentPortfolio.day_pnl_percent)}`}>
                {formatPercent(currentPortfolio.day_pnl_percent)}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner size="sm" />
            <span className="ml-2 text-gray-400">Loading portfolio data...</span>
          </div>
        )}

        {lastPortfolioUpdate && (
          <div className="mt-3 text-xs text-gray-500">
            Last updated: {lastPortfolioUpdate.toLocaleTimeString()}
          </div>
        )}
      </div>

      {/* Live Positions */}
      {showPositions && currentPositions.length > 0 && (
        <div className="bg-gray-800 rounded-lg p-4">
          <h4 className="text-white font-medium mb-3">Live Positions</h4>
          <div className="space-y-2">
            {currentPositions.slice(0, maxPositionsToShow).map((position, index) => (
              <div
                key={`${position.symbol}_${index}`}
                className="flex items-center justify-between bg-gray-700 rounded p-3"
              >
                <div className="flex items-center space-x-3">
                  <div>
                    <div className="text-white font-medium">{position.symbol}</div>
                    <div className="text-gray-400 text-sm">
                      {position.quantity.toLocaleString()} shares
                    </div>
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="text-white font-medium">
                    {formatCurrency(position.current_price * position.quantity)}
                  </div>
                  <div className={`text-sm ${getPnLColor(position.unrealized_pnl)}`}>
                    {formatCurrency(position.unrealized_pnl)} ({formatPercent(position.unrealized_pnl_percent)})
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {currentPositions.length > maxPositionsToShow && (
            <div className="text-gray-400 text-sm text-center mt-2">
              +{currentPositions.length - maxPositionsToShow} more positions
            </div>
          )}
        </div>
      )}

      {/* Recent Orders */}
      {showRecentOrders && currentOrders.length > 0 && (
        <div className="bg-gray-800 rounded-lg p-4">
          <h4 className="text-white font-medium mb-3">Recent Order Updates</h4>
          <div className="space-y-2">
            {currentOrders.slice(0, maxOrdersToShow).map((order, index) => (
              <div
                key={`${order.order_id}_${index}`}
                className="flex items-center justify-between bg-gray-700 rounded p-3"
              >
                <div className="flex items-center space-x-3">
                  <div>
                    <div className="text-white font-medium">
                      {order.trade_type} {order.symbol}
                    </div>
                    <div className="text-gray-400 text-sm">
                      {order.quantity.toLocaleString()} shares • {(order as any).order_type || 'ORDER'}
                    </div>
                  </div>
                </div>
                
                <div className="text-right">
                  <Badge variant={getOrderStatusColor(order.status)} size="sm">
                    {order.status}
                  </Badge>
                  <div className="text-gray-400 text-xs mt-1">
                    {formatTimestamp(order.timestamp)}
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {currentOrders.length > maxOrdersToShow && (
            <div className="text-gray-400 text-sm text-center mt-2">
              +{currentOrders.length - maxOrdersToShow} more orders
            </div>
          )}
        </div>
      )}

      {/* No Data State */}
      {(!currentPortfolio && !currentPositions.length && !currentOrders.length) && (
        <div className="bg-gray-800 rounded-lg p-8 text-center">
          <div className="text-gray-400">
            <div className="text-lg font-medium mb-2">No Trading Activity</div>
            <div className="text-sm">
              {isConnected 
                ? 'Connected and waiting for updates...'
                : 'Connect to WebSocket to see real-time updates'
              }
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Compact version for sidebars or small spaces
interface CompactPortfolioUpdatesProps {
  className?: string;
  showOnlyPnL?: boolean;
}

export const CompactPortfolioUpdates: React.FC<CompactPortfolioUpdatesProps> = ({
  className = '',
  showOnlyPnL = false,
}) => {
  const { mode } = useTradingContext();
  const portfolio = useAppSelector(selectPortfolio(mode));
  const isConnected = useAppSelector((state) => state.websocket.status === 'AUTHENTICATED');

  if (!portfolio) {
    return (
      <div className={`bg-gray-800 rounded p-3 ${className}`}>
        <div className="text-gray-400 text-center text-sm">
          {isConnected ? 'Loading...' : 'Offline'}
        </div>
      </div>
    );
  }

  const formatCurrency = (amount: number) => {
    if (Math.abs(amount) >= 1000000) {
      return `$${(amount / 1000000).toFixed(1)}M`;
    } else if (Math.abs(amount) >= 1000) {
      return `$${(amount / 1000).toFixed(1)}K`;
    }
    return `$${amount.toFixed(0)}`;
  };

  const getPnLColor = (value: number) => {
    if (value > 0) return 'text-green-400';
    if (value < 0) return 'text-red-400';
    return 'text-gray-300';
  };

  return (
    <div className={`bg-gray-800 rounded p-3 ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="text-gray-400 text-xs font-medium uppercase">{mode}</div>
        {isConnected && (
          <div className="h-2 w-2 bg-green-400 rounded-full animate-pulse" />
        )}
      </div>
      
      {!showOnlyPnL && (
        <div className="text-white text-sm font-medium mb-1">
          {formatCurrency(portfolio.total_value)}
        </div>
      )}
      
      <div className={`text-sm font-medium ${getPnLColor(portfolio.day_pnl)}`}>
        {formatCurrency(portfolio.day_pnl)} ({portfolio.day_pnl_percent >= 0 ? '+' : ''}{portfolio.day_pnl_percent.toFixed(2)}%)
      </div>
    </div>
  );
};

export default LivePortfolioUpdates;