import { useEffect, useRef, useCallback, useState, useContext } from 'react';
import { useAppDispatch } from '../store/hooks';
import {
  webSocketService,
  WebSocketStatus,
  WebSocketEventHandlers,
  MarketDataUpdate,
  OrderUpdate,
  PositionUpdate,
  PortfolioUpdate,
} from '../services/websocketService';
import TradingContext from '../contexts/TradingContext';

// Hook configuration
export interface UseWebSocketConfig {
  autoConnect?: boolean;
  subscribeToMarketData?: string[];
  subscribeToOrders?: boolean;
  subscribeToPortfolio?: boolean;
  onMarketData?: (data: MarketDataUpdate) => void;
  onOrderUpdate?: (data: OrderUpdate) => void;
  onPositionUpdate?: (data: PositionUpdate) => void;
  onPortfolioUpdate?: (data: PortfolioUpdate) => void;
}

export interface UseWebSocketReturn {
  status: WebSocketStatus;
  isConnected: boolean;
  connect: () => Promise<void>;
  disconnect: () => void;
  subscribe: (channel: string) => Promise<void>;
  unsubscribe: (channel: string) => Promise<void>;
  subscribeToMarketData: (symbols: string[]) => Promise<void>;
  subscribeToOrderUpdates: () => Promise<void>;
  subscribeToPortfolio: () => Promise<void>;
  error: string | null;
  lastConnected: Date | null;
  reconnectAttempts: number;
}

export const useWebSocket = (config: UseWebSocketConfig = {}): UseWebSocketReturn => {
  const {
    autoConnect = true,
    subscribeToMarketData = [],
    subscribeToOrders = false,
    subscribeToPortfolio = false,
    onMarketData,
    onOrderUpdate,
    onPositionUpdate,
    onPortfolioUpdate,
  } = config;

  const dispatch = useAppDispatch();
  // Use context safely - default to 'paper' mode if not within TradingContextProvider
  const tradingContext = useContext(TradingContext);
  const mode = tradingContext?.mode ?? 'paper';
  const [status, setStatus] = useState<WebSocketStatus>(webSocketService.getState().status);
  const [error, setError] = useState<string | null>(null);
  const isInitialized = useRef(false);
  const currentSubscriptions = useRef<Set<string>>(new Set());

  // Connection management
  const connect = useCallback(async () => {
    try {
      setError(null);
      await webSocketService.connect();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Connection failed';
      setError(errorMessage);
      throw err;
    }
  }, []);

  const disconnect = useCallback(() => {
    webSocketService.disconnect();
    currentSubscriptions.current.clear();
  }, []);

  // Subscription management
  const subscribe = useCallback(async (channel: string) => {
    try {
      await webSocketService.subscribe(channel);
      currentSubscriptions.current.add(channel);
    } catch (err) {
      console.error('Subscription failed:', err);
      throw err;
    }
  }, []);

  const unsubscribe = useCallback(async (channel: string) => {
    try {
      await webSocketService.unsubscribe(channel);
      currentSubscriptions.current.delete(channel);
    } catch (err) {
      console.error('Unsubscription failed:', err);
      throw err;
    }
  }, []);

  const subscribeToMarketDataHook = useCallback(async (symbols: string[]) => {
    try {
      await webSocketService.subscribeToMarketData(symbols);
      currentSubscriptions.current.add(`market_data:${symbols.join(',')}`);
    } catch (err) {
      console.error('Market data subscription failed:', err);
      throw err;
    }
  }, []);

  const subscribeToOrderUpdates = useCallback(async () => {
    try {
      await webSocketService.subscribeToOrderUpdates(mode);
      currentSubscriptions.current.add(`orders:${mode}`);
    } catch (err) {
      console.error('Order updates subscription failed:', err);
      throw err;
    }
  }, [mode]);

  const subscribeToPortfolioHook = useCallback(async () => {
    try {
      await webSocketService.subscribeToPortfolio(mode);
      currentSubscriptions.current.add(`portfolio:${mode}`);
    } catch (err) {
      console.error('Portfolio subscription failed:', err);
      throw err;
    }
  }, [mode]);

  // Event handlers setup
  useEffect(() => {
    const handlers: WebSocketEventHandlers = {
      onStatusChange: (newStatus: WebSocketStatus) => {
        setStatus(newStatus);
        
        // Clear error on successful connection
        if (newStatus === WebSocketStatus.AUTHENTICATED) {
          setError(null);
        }
      },
      
      onError: (errorMessage: string) => {
        setError(errorMessage);
      },
      
      onMarketData: (data: MarketDataUpdate) => {
        onMarketData?.(data);
        
        // Dispatch to Redux store if needed
        // dispatch(updateMarketData(data));
      },
      
      onOrderUpdate: (data: OrderUpdate) => {
        onOrderUpdate?.(data);
        
        // Invalidate trading queries on order updates
        // This ensures UI stays in sync with backend
        // dispatch(tradingApi.util.invalidateTags([
        //   { type: 'OrderHistory', id: `${data.paper_trading ? 'paper' : 'live'}_data` },
        //   { type: 'Portfolio', id: `${data.paper_trading ? 'paper' : 'live'}_data` },
        // ]));
      },
      
      onPositionUpdate: (data: PositionUpdate) => {
        onPositionUpdate?.(data);
        
        // Invalidate position and portfolio queries
        // dispatch(tradingApi.util.invalidateTags([
        //   { type: 'Position', id: `${data.paper_trading ? 'paper' : 'live'}_data` },
        //   { type: 'Portfolio', id: `${data.paper_trading ? 'paper' : 'live'}_data` },
        // ]));
      },
      
      onPortfolioUpdate: (data: PortfolioUpdate) => {
        onPortfolioUpdate?.(data);
        
        // Invalidate portfolio queries
        // dispatch(tradingApi.util.invalidateTags([
        //   { type: 'Portfolio', id: `${data.paper_trading ? 'paper' : 'live'}_data` },
        // ]));
      },
    };

    // Register event handlers
    Object.entries(handlers).forEach(([event, handler]) => {
      if (handler) {
        webSocketService.on(event as keyof WebSocketEventHandlers, handler as any);
      }
    });

    // Cleanup function
    return () => {
      Object.keys(handlers).forEach(event => {
        webSocketService.off(event as keyof WebSocketEventHandlers);
      });
    };
  }, [onMarketData, onOrderUpdate, onPositionUpdate, onPortfolioUpdate, dispatch]);

  // Auto-connect and initial subscriptions
  useEffect(() => {
    const initialize = async () => {
      if (!autoConnect || isInitialized.current) return;
      
      try {
        isInitialized.current = true;
        
        // Connect to WebSocket
        if (!webSocketService.isConnected()) {
          await connect();
        }

        // Wait a bit for connection to stabilize
        await new Promise(resolve => setTimeout(resolve, 100));

        // Set up initial subscriptions
        const subscriptionPromises: Promise<void>[] = [];

        // Market data subscription
        if (subscribeToMarketData.length > 0) {
          subscriptionPromises.push(subscribeToMarketDataHook(subscribeToMarketData));
        }

        // Order updates subscription
        if (subscribeToOrders) {
          subscriptionPromises.push(subscribeToOrderUpdates());
        }

        // Portfolio updates subscription
        if (subscribeToPortfolio) {
          subscriptionPromises.push(subscribeToPortfolioHook());
        }

        // Wait for all subscriptions to complete
        await Promise.all(subscriptionPromises);

      } catch (err) {
        console.error('WebSocket initialization failed:', err);
        setError(err instanceof Error ? err.message : 'Initialization failed');
      }
    };

    initialize();
  }, [
    autoConnect, 
    connect, 
    subscribeToMarketData, 
    subscribeToOrders, 
    subscribeToPortfolio,
    subscribeToMarketDataHook,
    subscribeToOrderUpdates,
    subscribeToPortfolioHook
  ]);

  // Handle trading mode changes
  useEffect(() => {
    const resubscribeForModeChange = async () => {
      if (!webSocketService.isConnected()) return;

      try {
        // Unsubscribe from old mode-specific channels
        const modeChannels = Array.from(currentSubscriptions.current).filter(
          channel => channel.includes('orders:') || channel.includes('portfolio:')
        );

        for (const channel of modeChannels) {
          await unsubscribe(channel);
        }

        // Re-subscribe with new mode
        if (subscribeToOrders) {
          await subscribeToOrderUpdates();
        }
        
        if (subscribeToPortfolio) {
          await subscribeToPortfolioHook();
        }
      } catch (err) {
        console.error('Failed to resubscribe after mode change:', err);
      }
    };

    resubscribeForModeChange();
  }, [mode, subscribeToOrders, subscribeToPortfolio, unsubscribe, subscribeToOrderUpdates, subscribeToPortfolioHook]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Don't disconnect on unmount as other components might be using the WebSocket
      // Instead, just clear our subscriptions
      currentSubscriptions.current.clear();
    };
  }, []);

  const wsState = webSocketService.getState();

  return {
    status,
    isConnected: webSocketService.isConnected(),
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    subscribeToMarketData: subscribeToMarketDataHook,
    subscribeToOrderUpdates,
    subscribeToPortfolio: subscribeToPortfolioHook,
    error,
    lastConnected: wsState.lastConnected,
    reconnectAttempts: wsState.reconnectAttempts,
  };
};

// Specialized hooks for common use cases
export const useMarketDataWebSocket = (symbols: string[]) => {
  const [marketData, setMarketData] = useState<Map<string, MarketDataUpdate>>(new Map());

  const ws = useWebSocket({
    subscribeToMarketData: symbols,
    onMarketData: (data: MarketDataUpdate) => {
      setMarketData(prev => new Map(prev.set(data.symbol, data)));
    },
  });

  return {
    ...ws,
    marketData: Object.fromEntries(marketData),
    getSymbolData: (symbol: string) => marketData.get(symbol),
  };
};

export const useTradingWebSocket = (mode: 'paper' | 'live') => {
  const [orders, setOrders] = useState<OrderUpdate[]>([]);
  const [positions, setPositions] = useState<Map<string, PositionUpdate>>(new Map());
  const [portfolio, setPortfolio] = useState<PortfolioUpdate | null>(null);

  const ws = useWebSocket({
    subscribeToOrders: true,
    subscribeToPortfolio: true,
    onOrderUpdate: (data: OrderUpdate) => {
      if (data.paper_trading === (mode === 'paper')) {
        setOrders(prev => [data, ...prev.slice(0, 99)]); // Keep last 100 orders
      }
    },
    onPositionUpdate: (data: PositionUpdate) => {
      if (data.paper_trading === (mode === 'paper')) {
        setPositions(prev => new Map(prev.set(data.symbol, data)));
      }
    },
    onPortfolioUpdate: (data: PortfolioUpdate) => {
      if (data.paper_trading === (mode === 'paper')) {
        setPortfolio(data);
      }
    },
  });

  return {
    ...ws,
    orders,
    positions: Object.fromEntries(positions),
    portfolio,
  };
};

export default useWebSocket;