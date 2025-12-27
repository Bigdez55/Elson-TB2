import React, { useEffect, useState } from 'react';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { connectWebSocket, disconnectWebSocket } from '../../store/slices/websocketSlice';
import { ConnectionStatusBanner } from '../common/ConnectionStatusBanner';
import { OrderNotification } from '../trading/LiveOrderUpdates';

interface LiveDataProviderProps {
  children: React.ReactNode;
  autoConnect?: boolean;
  showConnectionBanner?: boolean;
}

export const LiveDataProvider: React.FC<LiveDataProviderProps> = ({
  children,
  autoConnect = true,
  showConnectionBanner = true,
}) => {
  const dispatch = useAppDispatch();
  const websocketState = useAppSelector((state) => state.websocket);
  const [orderNotifications, setOrderNotifications] = useState<any[]>([]);
  const [isInitialized, setIsInitialized] = useState(false);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect && !isInitialized) {
      setIsInitialized(true);
      dispatch({ type: 'websocket/connectWebSocket' });
    }

    // Cleanup on unmount
    return () => {
      if (autoConnect) {
        dispatch({ type: 'websocket/disconnectWebSocket' });
      }
    };
  }, [autoConnect, dispatch, isInitialized]);

  // Handle order notifications
  useEffect(() => {
    const recentOrders = websocketState.recentOrders.slice(0, 5);
    const notifications = recentOrders
      .filter((order: any) => {
        // Only show notifications for filled or cancelled orders
        return order.status === 'filled' || order.status === 'cancelled';
      })
      .map((order: any) => ({
        id: order.order_id,
        order,
        timestamp: Date.now(),
      }));

    setOrderNotifications(notifications);
  }, [websocketState.recentOrders]);

  const dismissNotification = (id: string) => {
    setOrderNotifications(prev => prev.filter(n => n.id !== id));
  };

  // Auto-dismiss old notifications
  useEffect(() => {
    const interval = setInterval(() => {
      const fiveMinutesAgo = Date.now() - 5 * 60 * 1000;
      setOrderNotifications(prev => 
        prev.filter(n => n.timestamp > fiveMinutesAgo)
      );
    }, 60000); // Check every minute

    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      {/* Connection Status Banner */}
      {showConnectionBanner && (
        <ConnectionStatusBanner 
          showWhenConnected={false}
          autoHide={true}
        />
      )}

      {/* Main Content */}
      {children}

      {/* Order Notifications */}
      <div className="fixed top-16 right-4 z-50 space-y-2">
        {orderNotifications.map((notification) => (
          <OrderNotification
            key={notification.id}
            order={notification.order}
            onDismiss={() => dismissNotification(notification.id)}
          />
        ))}
      </div>

      {/* Global WebSocket Error */}
      {websocketState.error && websocketState.status === 'ERROR' && (
        <div className="fixed bottom-4 right-4 z-50">
          <div className="bg-red-900 border border-red-600 rounded-lg p-4 max-w-sm shadow-lg">
            <div className="flex items-start justify-between">
              <div>
                <div className="text-red-100 font-medium mb-1">
                  WebSocket Connection Error
                </div>
                <div className="text-red-200 text-sm">
                  {websocketState.error}
                </div>
                <button
                  onClick={() => dispatch({ type: 'websocket/connectWebSocket' })}
                  className="mt-2 text-red-300 hover:text-red-100 text-sm underline"
                >
                  Retry Connection
                </button>
              </div>
              <button
                onClick={() => dispatch({ type: 'websocket/clearError' })}
                className="text-red-300 hover:text-red-100 transition-colors"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Debug Information (Development Only) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="fixed bottom-4 left-4 z-40">
          <details className="bg-gray-900 border border-gray-700 rounded p-2 text-xs text-gray-400">
            <summary className="cursor-pointer">WebSocket Debug</summary>
            <div className="mt-2 space-y-1">
              <div>Status: {websocketState.status}</div>
              <div>Messages: {websocketState.messageCount}</div>
              <div>Channels: {websocketState.subscribedChannels.length}</div>
              <div>Orders: {websocketState.recentOrders.length}</div>
              <div>Market Data: {Object.keys(websocketState.marketData).length}</div>
              <div>Positions: {Object.keys(websocketState.positions).length}</div>
              {websocketState.lastMessageTime && (
                <div>Last: {new Date(websocketState.lastMessageTime).toLocaleTimeString()}</div>
              )}
            </div>
          </details>
        </div>
      )}
    </div>
  );
};

// Hook for manual WebSocket control
export const useWebSocketControl = () => {
  const dispatch = useAppDispatch();
  const websocketState = useAppSelector((state) => state.websocket);

  const connect = () => {
    dispatch({ type: 'websocket/connectWebSocket' });
  };

  const disconnect = () => {
    dispatch({ type: 'websocket/disconnectWebSocket' });
  };

  const subscribeToSymbol = async (symbol: string) => {
    dispatch({ 
      type: 'websocket/subscribeToChannel', 
      payload: `market_data:${symbol}` 
    });
  };

  const unsubscribeFromSymbol = async (symbol: string) => {
    dispatch({ 
      type: 'websocket/unsubscribeFromChannel', 
      payload: `market_data:${symbol}` 
    });
  };

  return {
    connect,
    disconnect,
    subscribeToSymbol,
    unsubscribeFromSymbol,
    state: websocketState,
    isConnected: websocketState.status === 'AUTHENTICATED',
  };
};

export default LiveDataProvider;