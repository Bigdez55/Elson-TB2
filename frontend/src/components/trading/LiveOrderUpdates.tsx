import React, { useEffect, useState } from 'react';
import { useAppSelector } from '../../store/hooks';
import { selectRecentOrders } from '../../store/slices/websocketSlice';
import { useTradingContext } from '../../contexts/TradingContext';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';

interface LiveOrderUpdatesProps {
  className?: string;
  maxOrdersToShow?: number;
  showFilters?: boolean;
  onOrderClick?: (orderId: string) => void;
}

export const LiveOrderUpdates: React.FC<LiveOrderUpdatesProps> = ({
  className = '',
  maxOrdersToShow = 10,
  showFilters = true,
  onOrderClick,
}) => {
  const { mode } = useTradingContext();
  const allOrders = useAppSelector(selectRecentOrders);
  const isConnected = useAppSelector((state) => state.websocket.status === 'AUTHENTICATED');
  
  const [filter, setFilter] = useState<'all' | 'filled' | 'pending' | 'cancelled'>('all');
  const [newOrdersCount, setNewOrdersCount] = useState(0);
  const [lastOrderId, setLastOrderId] = useState<string | null>(null);

  // Filter orders by current trading mode
  const modeOrders = allOrders.filter(order => 
    order.paper_trading === (mode === 'paper')
  );

  // Apply status filter
  const filteredOrders = filter === 'all' 
    ? modeOrders 
    : modeOrders.filter(order => order.status.toLowerCase() === filter);

  // Limit displayed orders
  const displayOrders = filteredOrders.slice(0, maxOrdersToShow);

  // Track new orders for notifications
  useEffect(() => {
    if (modeOrders.length > 0) {
      const latestOrder = modeOrders[0];
      if (lastOrderId && latestOrder.order_id !== lastOrderId) {
        setNewOrdersCount(prev => prev + 1);
        // Auto-clear new order notification after 5 seconds
        setTimeout(() => setNewOrdersCount(0), 5000);
      }
      setLastOrderId(latestOrder.order_id);
    }
  }, [modeOrders, lastOrderId]);

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    
    return date.toLocaleDateString();
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const getOrderStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'filled': return 'success';
      case 'partial_fill': return 'warning';
      case 'cancelled': return 'error';
      case 'pending': return 'info';
      case 'rejected': return 'error';
      default: return 'neutral';
    }
  };

  const getTradeTypeColor = (tradeType: string) => {
    return tradeType === 'BUY' ? 'text-green-400' : 'text-red-400';
  };

  const getOrderProgress = (order: any) => {
    if (!order.filled_quantity || order.filled_quantity === 0) return 0;
    return (order.filled_quantity / order.quantity) * 100;
  };

  const clearNewOrdersNotification = () => {
    setNewOrdersCount(0);
  };

  return (
    <div className={`bg-gray-800 rounded-lg p-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <h3 className="text-lg font-medium text-white">Live Order Updates</h3>
          <Badge variant={mode === 'paper' ? 'warning' : 'info'} size="sm">
            {mode.toUpperCase()}
          </Badge>
          {isConnected && (
            <Badge variant="success" size="sm">Live</Badge>
          )}
          {newOrdersCount > 0 && (
            <Badge variant="info" size="sm">
              {newOrdersCount} new
            </Badge>
          )}
        </div>
        
        {newOrdersCount > 0 && (
          <Button size="sm" variant="outline" onClick={clearNewOrdersNotification}>
            Clear
          </Button>
        )}
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="flex space-x-2 mb-4">
          {['all', 'filled', 'pending', 'cancelled'].map((filterOption) => (
            <button
              key={filterOption}
              onClick={() => setFilter(filterOption as any)}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                filter === filterOption
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {filterOption.charAt(0).toUpperCase() + filterOption.slice(1)}
            </button>
          ))}
        </div>
      )}

      {/* Order List */}
      {displayOrders.length > 0 ? (
        <div className="space-y-3">
          {displayOrders.map((order, index) => (
            <div
              key={`${order.order_id}_${index}`}
              className={`bg-gray-700 rounded-lg p-4 transition-all duration-200 ${
                onOrderClick ? 'cursor-pointer hover:bg-gray-600' : ''
              }`}
              onClick={() => onOrderClick?.(order.order_id)}
            >
              {/* Order Header */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-3">
                  <span className={`font-bold ${getTradeTypeColor(order.trade_type)}`}>
                    {order.trade_type}
                  </span>
                  <span className="text-white font-medium">{order.symbol}</span>
                  <Badge variant="neutral" size="sm">{(order as any).order_type || order.trade_type}</Badge>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Badge variant={getOrderStatusColor(order.status)} size="sm">
                    {order.status}
                  </Badge>
                  <span className="text-gray-400 text-xs">
                    {formatTimestamp(order.timestamp)}
                  </span>
                </div>
              </div>

              {/* Order Details */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                <div>
                  <span className="text-gray-400">Quantity:</span>
                  <span className="text-white ml-1 font-medium">
                    {order.quantity.toLocaleString()}
                  </span>
                </div>
                
                {order.price && (
                  <div>
                    <span className="text-gray-400">Price:</span>
                    <span className="text-white ml-1 font-medium">
                      {formatCurrency(order.price)}
                    </span>
                  </div>
                )}
                
                {order.filled_quantity && order.filled_quantity > 0 && (
                  <div>
                    <span className="text-gray-400">Filled:</span>
                    <span className="text-white ml-1 font-medium">
                      {order.filled_quantity.toLocaleString()}
                    </span>
                  </div>
                )}
                
                {order.filled_price && (
                  <div>
                    <span className="text-gray-400">Avg Price:</span>
                    <span className="text-white ml-1 font-medium">
                      {formatCurrency(order.filled_price)}
                    </span>
                  </div>
                )}
              </div>

              {/* Execution Progress for Partial Fills */}
              {order.filled_quantity && order.filled_quantity > 0 && order.filled_quantity < order.quantity && (
                <div className="mt-3">
                  <div className="flex justify-between text-xs text-gray-400 mb-1">
                    <span>Execution Progress</span>
                    <span>{Math.round(getOrderProgress(order))}%</span>
                  </div>
                  <div className="w-full bg-gray-600 rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${getOrderProgress(order)}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Order ID for reference */}
              <div className="mt-2 text-xs text-gray-500">
                Order ID: {order.order_id}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8">
          <div className="text-gray-400 mb-2">
            {isConnected ? (
              <>
                <svg className="h-8 w-8 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <div>No {filter === 'all' ? '' : filter} orders</div>
                <div className="text-xs text-gray-500">
                  {filter === 'all' 
                    ? 'Order updates will appear here in real-time'
                    : `No ${filter} orders found`
                  }
                </div>
              </>
            ) : (
              <>
                <svg className="h-8 w-8 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18.364 5.636l-12.728 12.728M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z" />
                </svg>
                <div>Not Connected</div>
                <div className="text-xs text-gray-500">
                  Connect to WebSocket to see live order updates
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Show More */}
      {filteredOrders.length > maxOrdersToShow && (
        <div className="mt-4 text-center">
          <div className="text-gray-400 text-sm">
            Showing {maxOrdersToShow} of {filteredOrders.length} orders
          </div>
        </div>
      )}

      {/* Connection Status */}
      <div className="mt-4 pt-3 border-t border-gray-700">
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-500">Real-time Updates</span>
          <span className={isConnected ? 'text-green-400' : 'text-red-400'}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>
    </div>
  );
};

// Notification component for new order updates
interface OrderNotificationProps {
  order: any;
  onDismiss: () => void;
  className?: string;
}

export const OrderNotification: React.FC<OrderNotificationProps> = ({
  order,
  onDismiss,
  className = '',
}) => {
  useEffect(() => {
    // Auto-dismiss after 5 seconds
    const timer = setTimeout(onDismiss, 5000);
    return () => clearTimeout(timer);
  }, [onDismiss]);

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'filled': return 'bg-green-900 border-green-600 text-green-100';
      case 'cancelled': return 'bg-red-900 border-red-600 text-red-100';
      default: return 'bg-blue-900 border-blue-600 text-blue-100';
    }
  };

  return (
    <div className={`fixed top-4 right-4 z-50 max-w-sm ${className}`}>
      <div className={`border rounded-lg p-4 shadow-lg ${getStatusColor(order.status)}`}>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="font-medium mb-1">
              Order {order.status}: {order.trade_type} {order.symbol}
            </div>
            <div className="text-sm opacity-90">
              {order.quantity.toLocaleString()} shares
              {order.filled_price && ` at ${order.filled_price.toFixed(2)}`}
            </div>
          </div>
          <button
            onClick={onDismiss}
            className="opacity-70 hover:opacity-100 transition-opacity"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default LiveOrderUpdates;