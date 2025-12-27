import { useState, useEffect, useCallback, useRef } from 'react';
import { useDispatch } from 'react-redux';
import webSocketService, { MarketDataUpdate, WebSocketStatus } from '../services/websocketService';
import { MarketQuote } from '../types';

// Re-export for convenience
export type { MarketQuote };

export interface UseMarketWebSocketProps {
  autoConnect?: boolean;
  reconnectAttempts?: number;
  reconnectDelay?: number;
}

export interface UseMarketWebSocketReturn {
  isConnected: boolean;
  error: string | null;
  quotes: Record<string, MarketQuote>;
  subscribe: (symbols: string[]) => void;
  unsubscribe: (symbols: string[]) => void;
  connect: () => void;
  disconnect: () => void;
}

export const useMarketWebSocket = ({
  autoConnect = false,
}: UseMarketWebSocketProps = {}): UseMarketWebSocketReturn => {
  const dispatch = useDispatch();
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [quotes, setQuotes] = useState<Record<string, MarketQuote>>({});
  const subscribedSymbolsRef = useRef<Set<string>>(new Set());

  // Convert MarketDataUpdate to MarketQuote format
  const convertToMarketQuote = (update: MarketDataUpdate): MarketQuote => ({
    symbol: update.symbol,
    price: update.price,
    timestamp: new Date(update.timestamp).getTime(),
    volume: update.volume,
    high24h: update.price * 1.02, // Approximation - would come from server in real impl
    low24h: update.price * 0.98,
    change24h: update.change,
  });

  // Handle market data updates
  const handleMarketData = useCallback((data: MarketDataUpdate) => {
    const quote = convertToMarketQuote(data);
    setQuotes(prev => ({
      ...prev,
      [quote.symbol]: quote,
    }));
  }, []);

  // Handle status changes
  const handleStatusChange = useCallback((status: WebSocketStatus) => {
    const connected = status === WebSocketStatus.AUTHENTICATED || status === WebSocketStatus.CONNECTED;
    setIsConnected(connected);

    if (status === WebSocketStatus.ERROR || status === WebSocketStatus.AUTHORIZATION_FAILED) {
      const state = webSocketService.getState();
      setError(state.error || 'WebSocket connection failed');
    } else {
      setError(null);
    }
  }, []);

  // Handle errors
  const handleError = useCallback((errorMessage: string) => {
    setError(errorMessage);
  }, []);

  // Connect to WebSocket
  const connect = useCallback(async () => {
    try {
      setError(null);
      await webSocketService.connect();

      // Re-subscribe to previously subscribed symbols
      if (subscribedSymbolsRef.current.size > 0) {
        const symbols = Array.from(subscribedSymbolsRef.current);
        await webSocketService.subscribeToMarketData(symbols);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to connect to WebSocket';
      setError(errorMsg);
      console.error('WebSocket connection error:', err);
    }
  }, []);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    webSocketService.disconnect();
    setIsConnected(false);
    setQuotes({});
  }, []);

  // Subscribe to market data for symbols
  const subscribe = useCallback(async (symbols: string[]) => {
    if (symbols.length === 0) return;

    // Track subscribed symbols
    symbols.forEach(symbol => subscribedSymbolsRef.current.add(symbol.toUpperCase()));

    // Subscribe via WebSocket
    try {
      await webSocketService.subscribeToMarketData(symbols.map(s => s.toUpperCase()));
    } catch (err) {
      console.error('Failed to subscribe to market data:', err);
      setError('Failed to subscribe to market data');
    }
  }, []);

  // Unsubscribe from market data
  const unsubscribe = useCallback((symbols: string[]) => {
    if (symbols.length === 0) return;

    // Remove from tracked symbols
    symbols.forEach(symbol => subscribedSymbolsRef.current.delete(symbol.toUpperCase()));

    // Remove quotes for unsubscribed symbols
    setQuotes(prev => {
      const updated = { ...prev };
      symbols.forEach(symbol => {
        delete updated[symbol.toUpperCase()];
      });
      return updated;
    });

    // Note: WebSocket service doesn't have symbol-specific unsubscribe
    // It unsubscribes from channels. If needed, implement channel management.
  }, []);

  // Set up WebSocket event handlers
  useEffect(() => {
    webSocketService.on('onMarketData', handleMarketData);
    webSocketService.on('onStatusChange', handleStatusChange);
    webSocketService.on('onError', handleError);

    // Check initial connection status
    const state = webSocketService.getState();
    handleStatusChange(state.status);

    return () => {
      webSocketService.off('onMarketData');
      webSocketService.off('onStatusChange');
      webSocketService.off('onError');
    };
  }, [handleMarketData, handleStatusChange, handleError]);

  // Auto-connect on mount if requested
  useEffect(() => {
    if (autoConnect && !isConnected) {
      connect();
    }

    return () => {
      if (autoConnect) {
        disconnect();
      }
    };
  }, [autoConnect]); // Only run on mount/unmount

  return {
    isConnected,
    error,
    quotes,
    subscribe,
    unsubscribe,
    connect,
    disconnect,
  };
};
