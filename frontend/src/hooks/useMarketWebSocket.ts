import { useState, useEffect, useCallback } from 'react';
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
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [quotes, setQuotes] = useState<Record<string, MarketQuote>>({});
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [subscribedSymbols, setSubscribedSymbols] = useState<Set<string>>(new Set());

  const connect = useCallback(() => {
    try {
      // Mock WebSocket connection for demo purposes
      // In a real implementation, this would connect to your WebSocket server
      const mockWs = {
        readyState: WebSocket.OPEN,
        close: () => {},
        send: () => {},
      } as any;

      setWs(mockWs);
      setIsConnected(true);
      setError(null);

      // Simulate real-time price updates
      const interval = setInterval(() => {
        setQuotes(prev => {
          const updated = { ...prev };
          subscribedSymbols.forEach(symbol => {
            const basePrice = prev[symbol]?.price || Math.random() * 100 + 50;
            const change = (Math.random() - 0.5) * 2; // -1 to 1
            updated[symbol] = {
              symbol,
              price: Math.max(0.01, basePrice + change),
              timestamp: Date.now(),
              volume: Math.random() * 1000000,
              high24h: basePrice * 1.1,
              low24h: basePrice * 0.9,
              change24h: change,
            };
          });
          return updated;
        });
      }, 2000);

      // Store interval for cleanup
      (mockWs as any)._interval = interval;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect');
      setIsConnected(false);
    }
  }, [subscribedSymbols]);

  const disconnect = useCallback(() => {
    if (ws) {
      if ((ws as any)._interval) {
        clearInterval((ws as any)._interval);
      }
      ws.close();
      setWs(null);
      setIsConnected(false);
    }
  }, [ws]);

  const subscribe = useCallback((symbols: string[]) => {
    setSubscribedSymbols(prev => {
      const newSet = new Set(prev);
      symbols.forEach(symbol => newSet.add(symbol.toUpperCase()));
      return newSet;
    });

    // Initialize quotes for new symbols
    symbols.forEach(symbol => {
      const upperSymbol = symbol.toUpperCase();
      setQuotes(prev => {
        if (!prev[upperSymbol]) {
          return {
            ...prev,
            [upperSymbol]: {
              symbol: upperSymbol,
              price: Math.random() * 100 + 50,
              timestamp: Date.now(),
              volume: Math.random() * 1000000,
              high24h: 0,
              low24h: 0,
              change24h: 0,
            },
          };
        }
        return prev;
      });
    });
  }, []);

  const unsubscribe = useCallback((symbols: string[]) => {
    setSubscribedSymbols(prev => {
      const newSet = new Set(prev);
      symbols.forEach(symbol => newSet.delete(symbol.toUpperCase()));
      return newSet;
    });

    setQuotes(prev => {
      const updated = { ...prev };
      symbols.forEach(symbol => {
        delete updated[symbol.toUpperCase()];
      });
      return updated;
    });
  }, []);

  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoConnect]);

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