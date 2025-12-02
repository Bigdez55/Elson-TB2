import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useSelector } from 'react-redux';
import { cacheGet, cacheSet } from '../utils/cacheUtils';

// Define WebSocket message types
export interface MarketQuote {
  symbol: string;
  price: number;
  bid?: number;
  ask?: number;
  volume?: number;
  timestamp: string;
  source: string;
  trade_id?: string;
}

interface SubscriptionMessage {
  action: 'subscribe' | 'unsubscribe';
  symbols: string[];
}

interface PingMessage {
  action: 'ping';
}

interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

interface UseMarketWebSocketProps {
  symbols?: string[];
  autoConnect?: boolean;
  token?: string;
  cacheEnabled?: boolean;
  cacheTTL?: number;
}

interface UseMarketWebSocketResult {
  isConnected: boolean;
  error: string | null;
  quotes: Record<string, MarketQuote>;
  subscribe: (symbols: string[]) => void;
  unsubscribe: (symbols: string[]) => void;
  reconnect: () => void;
}

/**
 * Custom hook for connecting to market data WebSocket service
 * 
 * @param {UseMarketWebSocketProps} props - Configuration options
 * @returns {UseMarketWebSocketResult} WebSocket connection controls and data
 */
// Global cache for sharing quotes between hook instances
const GLOBAL_QUOTES_CACHE: Record<string, MarketQuote> = {};

// Global connection reference to prevent multiple connections
let globalWsConnection: WebSocket | null = null;
let globalConnectionCount = 0;

export const useMarketWebSocket = ({
  symbols = [],
  autoConnect = true,
  token,
  cacheEnabled = true,
  cacheTTL = 300 // 5 minutes default cache TTL
}: UseMarketWebSocketProps = {}): UseMarketWebSocketResult => {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [quotes, setQuotes] = useState<Record<string, MarketQuote>>({});
  
  const wsRef = useRef<WebSocket | null>(null);
  const pingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const subscriptionsRef = useRef<Set<string>>(new Set(symbols));
  // Refs for batch updates
  const pendingUpdatesRef = useRef<Record<string, MarketQuote>>({});
  const updateIntervalRef = useRef<number | null>(null);
  
  // Get auth token from redux
  const authToken = useSelector((state: any) => state.user?.token) || token;
  
  // Reconnect with exponential backoff
  const reconnectBackoff = useRef<number>(1000);
  const maxReconnectDelay = 30000; // 30 seconds
  
  // Define WebSocket URL based on environment
  const getWebSocketUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = import.meta.env.VITE_API_BASE_URL || window.location.host;
    let url = `${protocol}//${host}/ws/market/feed`;
    
    // Add auth token if available
    if (authToken) {
      url += `?token=${authToken}`;
    }
    
    return url;
  }, [authToken]);
  
  /**
   * Connect to the WebSocket server
   */
  // Initialize with cached quotes if available
  useEffect(() => {
    if (cacheEnabled) {
      // Try to initialize from global memory cache first (fastest)
      const initialQuotes: Record<string, MarketQuote> = {};
      let foundCachedData = false;
      
      symbols.forEach(symbol => {
        const normalizedSymbol = symbol.toUpperCase();
        
        // Check global memory cache first
        if (GLOBAL_QUOTES_CACHE[normalizedSymbol]) {
          initialQuotes[normalizedSymbol] = GLOBAL_QUOTES_CACHE[normalizedSymbol];
          foundCachedData = true;
        } else {
          // Check localStorage cache
          const cachedQuote = cacheGet<MarketQuote>(`market_quote:${normalizedSymbol}`);
          if (cachedQuote) {
            initialQuotes[normalizedSymbol] = cachedQuote;
            // Update global cache too
            GLOBAL_QUOTES_CACHE[normalizedSymbol] = cachedQuote;
            foundCachedData = true;
          }
        }
      });
      
      if (foundCachedData) {
        setQuotes(prev => ({...prev, ...initialQuotes}));
      }
    }
  }, [symbols, cacheEnabled]);

  const connect = useCallback(() => {
    // Use global connection if available
    if (globalWsConnection?.readyState === WebSocket.OPEN) {
      console.log('Using existing global WebSocket connection');
      wsRef.current = globalWsConnection;
      globalConnectionCount++;
      
      // Set connected state
      setIsConnected(true);
      setError(null);
      
      // Re-subscribe to symbols
      if (subscriptionsRef.current.size > 0) {
        const subscribeMsg: SubscriptionMessage = {
          action: 'subscribe',
          symbols: Array.from(subscriptionsRef.current)
        };
        globalWsConnection.send(JSON.stringify(subscribeMsg));
      }
      
      return;
    }
    
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }
    
    try {
      // Close existing connection if any
      if (wsRef.current) {
        wsRef.current.close();
      }
      
      // Create new WebSocket connection
      const ws = new WebSocket(getWebSocketUrl());
      wsRef.current = ws;
      
      // Set as global connection
      globalWsConnection = ws;
      globalConnectionCount++;
      
      ws.onopen = () => {
        console.log('Market WebSocket connected');
        setIsConnected(true);
        setError(null);
        reconnectBackoff.current = 1000; // Reset backoff on successful connection
        
        // Re-subscribe to previously subscribed symbols
        if (subscriptionsRef.current.size > 0) {
          const subscribeMsg: SubscriptionMessage = {
            action: 'subscribe',
            symbols: Array.from(subscriptionsRef.current)
          };
          ws.send(JSON.stringify(subscribeMsg));
        }
        
        // Start ping interval to keep connection alive
        if (pingTimerRef.current) {
          clearInterval(pingTimerRef.current);
        }
        
        pingTimerRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            const pingMsg: PingMessage = { action: 'ping' };
            ws.send(JSON.stringify(pingMsg));
          }
        }, 30000); // Send ping every 30 seconds
      };
      
      // Use the refs that are defined at the top level for message handling
      
      // Optimized message handler
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Handle different message types
          if (data.type === 'subscribed') {
            console.log('Subscribed to:', data.symbols);
          } else if (data.type === 'unsubscribed') {
            console.log('Unsubscribed from:', data.symbols);
          } else if (data.type === 'error') {
            console.error('WebSocket error:', data.message);
            setError(data.message);
          } else if (data.type === 'pong') {
            // Heartbeat response, just ignore
          } else if (data.symbol) {
            // This is a market data update
            const symbol = data.symbol;
            
            // Store in pending updates to batch React state updates
            pendingUpdatesRef.current[symbol] = data;
            
            // Update global cache
            GLOBAL_QUOTES_CACHE[symbol] = data;
            
            // Store in localStorage cache if enabled
            if (cacheEnabled) {
              cacheSet(`market_quote:${symbol}`, data, cacheTTL);
            }
            
            // Set up interval to batch updates if not already running
            if (!updateIntervalRef.current) {
              updateIntervalRef.current = window.setInterval(() => {
                if (Object.keys(pendingUpdatesRef.current).length > 0) {
                  setQuotes(prev => ({
                    ...prev,
                    ...pendingUpdatesRef.current
                  }));
                  pendingUpdatesRef.current = {};
                }
              }, 100); // Batch updates every 100ms
            }
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };
      
      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection error');
      };
      
      ws.onclose = (event) => {
        console.log(`WebSocket closed: ${event.code} ${event.reason}`);
        setIsConnected(false);
        
        // Clear ping timer
        if (pingTimerRef.current) {
          clearInterval(pingTimerRef.current);
          pingTimerRef.current = null;
        }
        
        // Schedule reconnect with exponential backoff
        if (!event.wasClean) {
          const delay = Math.min(reconnectBackoff.current, maxReconnectDelay);
          console.log(`Scheduling reconnect in ${delay}ms`);
          
          if (reconnectTimerRef.current) {
            clearTimeout(reconnectTimerRef.current);
          }
          
          reconnectTimerRef.current = setTimeout(() => {
            console.log('Attempting to reconnect...');
            connect();
          }, delay);
          
          // Increase backoff for next attempt
          reconnectBackoff.current = Math.min(reconnectBackoff.current * 1.5, maxReconnectDelay);
        }
      };
    } catch (err) {
      console.error('Error creating WebSocket:', err);
      setError('Failed to create WebSocket connection');
    }
  }, [getWebSocketUrl]);
  
  /**
   * Subscribe to market data for symbols
   */
  const subscribe = useCallback((symbols: string[]) => {
    if (!symbols || symbols.length === 0) return;
    
    // Normalize symbols to uppercase
    const normalizedSymbols = symbols.map(s => s.trim().toUpperCase());
    
    // Update subscriptions
    normalizedSymbols.forEach(s => subscriptionsRef.current.add(s));
    
    // Send subscription message if connected
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const subscribeMsg: SubscriptionMessage = {
        action: 'subscribe',
        symbols: normalizedSymbols
      };
      wsRef.current.send(JSON.stringify(subscribeMsg));
    } else if (!wsRef.current && globalWsConnection && globalWsConnection.readyState === WebSocket.OPEN) {
      // If we're using the global connection
      const subscribeMsg: SubscriptionMessage = {
        action: 'subscribe',
        symbols: normalizedSymbols
      };
      globalWsConnection.send(JSON.stringify(subscribeMsg));
    } else {
      // Will be subscribed when connection is established
      console.log('WebSocket not connected, subscription pending connection');
    }
  }, []);
  
  /**
   * Unsubscribe from market data for symbols
   */
  const unsubscribe = useCallback((symbols: string[]) => {
    if (!symbols || symbols.length === 0) return;
    
    // Normalize symbols to uppercase
    const normalizedSymbols = symbols.map(s => s.trim().toUpperCase());
    
    // Update subscriptions
    normalizedSymbols.forEach(s => subscriptionsRef.current.delete(s));
    
    // Remove from quotes
    setQuotes(prev => {
      const newQuotes = { ...prev };
      normalizedSymbols.forEach(symbol => {
        delete newQuotes[symbol];
      });
      return newQuotes;
    });
    
    // Send unsubscription message if connected
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const unsubscribeMsg: SubscriptionMessage = {
        action: 'unsubscribe',
        symbols: normalizedSymbols
      };
      wsRef.current.send(JSON.stringify(unsubscribeMsg));
    } else if (!wsRef.current && globalWsConnection && globalWsConnection.readyState === WebSocket.OPEN) {
      // If we're using the global connection
      const unsubscribeMsg: SubscriptionMessage = {
        action: 'unsubscribe',
        symbols: normalizedSymbols
      };
      globalWsConnection.send(JSON.stringify(unsubscribeMsg));
    }
  }, []);
  
  /**
   * Manually reconnect to the WebSocket
   */
  const reconnect = useCallback(() => {
    console.log('Manual reconnect requested');
    if (wsRef.current) {
      wsRef.current.close();
    }
    connect();
  }, [connect]);
  
  // Connect on mount if autoConnect is true
  useEffect(() => {
    if (autoConnect) {
      connect();
    }
    
    // Add initial symbols if provided
    if (symbols && symbols.length > 0) {
      subscribe(symbols);
    }
    
    // Clean up on unmount
    return () => {
      // Decrement connection count
      globalConnectionCount--;
      
      // If this is the last instance using the connection, close it
      if (globalConnectionCount <= 0 && globalWsConnection) {
        globalWsConnection.close();
        globalWsConnection = null;
        globalConnectionCount = 0;
      }
      
      // Cleanup local reference
      wsRef.current = null;
      
      // Clear timers
      if (pingTimerRef.current) {
        clearInterval(pingTimerRef.current);
        pingTimerRef.current = null;
      }
      
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      
      // Clear the batch update interval
      if (updateIntervalRef.current) {
        clearInterval(updateIntervalRef.current);
        updateIntervalRef.current = null;
      }
      
      // Unsubscribe from all symbols
      subscriptionsRef.current.clear();
    };
  }, [connect, autoConnect, symbols, subscribe]);
  
  return {
    isConnected,
    error,
    quotes,
    subscribe,
    unsubscribe,
    reconnect
  };
};

export default useMarketWebSocket;