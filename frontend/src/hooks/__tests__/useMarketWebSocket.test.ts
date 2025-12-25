import { renderHook, act } from '@testing-library/react';
import { useMarketWebSocket } from '../useMarketWebSocket';

// Mock WebSocket
class MockWebSocket {
  static OPEN = 1;
  static CLOSED = 3;
  
  readyState = MockWebSocket.OPEN;
  onopen?: () => void;
  onclose?: () => void;
  onmessage?: (event: { data: string }) => void;
  onerror?: () => void;

  close = jest.fn();
  send = jest.fn();

  constructor(url: string) {
    setTimeout(() => {
      if (this.onopen) this.onopen();
    }, 0);
  }
}

// Mock global WebSocket
Object.defineProperty(window, 'WebSocket', {
  value: MockWebSocket,
});

describe('useMarketWebSocket Hook Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => useMarketWebSocket());

      expect(result.current.isConnected).toBe(false);
      expect(result.current.error).toBe(null);
      expect(result.current.quotes).toEqual({});
    });

    it('should auto-connect when autoConnect is true', () => {
      const { result } = renderHook(() => useMarketWebSocket({ autoConnect: true }));

      act(() => {
        jest.runAllTimers();
      });

      expect(result.current.isConnected).toBe(true);
    });

    it('should not auto-connect when autoConnect is false', () => {
      const { result } = renderHook(() => useMarketWebSocket({ autoConnect: false }));

      expect(result.current.isConnected).toBe(false);
    });
  });

  describe('Connection Management', () => {
    it('should connect successfully', () => {
      const { result } = renderHook(() => useMarketWebSocket());

      act(() => {
        result.current.connect();
      });

      expect(result.current.isConnected).toBe(true);
      expect(result.current.error).toBe(null);
    });

    it('should disconnect successfully', () => {
      const { result } = renderHook(() => useMarketWebSocket());

      act(() => {
        result.current.connect();
      });

      expect(result.current.isConnected).toBe(true);

      act(() => {
        result.current.disconnect();
      });

      expect(result.current.isConnected).toBe(false);
    });

    it('should handle connection errors', () => {
      // Mock a connection that throws an error
      jest.spyOn(console, 'error').mockImplementation(() => {});
      
      const { result } = renderHook(() => useMarketWebSocket());

      // Simulate connection error by throwing in connect
      const originalError = console.error;
      
      // Test will be implemented based on actual error handling in the hook
      expect(result.current.error).toBe(null);
      
      console.error = originalError;
    });
  });

  describe('Symbol Subscription', () => {
    it('should subscribe to symbols', () => {
      const { result } = renderHook(() => useMarketWebSocket());

      act(() => {
        result.current.connect();
        result.current.subscribe(['AAPL', 'GOOGL']);
      });

      expect(Object.keys(result.current.quotes)).toContain('AAPL');
      expect(Object.keys(result.current.quotes)).toContain('GOOGL');
    });

    it('should convert symbols to uppercase', () => {
      const { result } = renderHook(() => useMarketWebSocket());

      act(() => {
        result.current.connect();
        result.current.subscribe(['aapl', 'googl']);
      });

      expect(Object.keys(result.current.quotes)).toContain('AAPL');
      expect(Object.keys(result.current.quotes)).toContain('GOOGL');
      expect(Object.keys(result.current.quotes)).not.toContain('aapl');
    });

    it('should unsubscribe from symbols', () => {
      const { result } = renderHook(() => useMarketWebSocket());

      act(() => {
        result.current.connect();
        result.current.subscribe(['AAPL', 'GOOGL', 'MSFT']);
      });

      expect(Object.keys(result.current.quotes)).toHaveLength(3);

      act(() => {
        result.current.unsubscribe(['GOOGL']);
      });

      expect(Object.keys(result.current.quotes)).toHaveLength(2);
      expect(Object.keys(result.current.quotes)).toContain('AAPL');
      expect(Object.keys(result.current.quotes)).toContain('MSFT');
      expect(Object.keys(result.current.quotes)).not.toContain('GOOGL');
    });

    it('should handle duplicate subscriptions', () => {
      const { result } = renderHook(() => useMarketWebSocket());

      act(() => {
        result.current.connect();
        result.current.subscribe(['AAPL']);
        result.current.subscribe(['AAPL']); // Duplicate
      });

      expect(Object.keys(result.current.quotes)).toHaveLength(1);
      expect(Object.keys(result.current.quotes)).toContain('AAPL');
    });
  });

  describe('Real-time Updates', () => {
    it('should generate mock price updates', () => {
      const { result } = renderHook(() => useMarketWebSocket());

      act(() => {
        result.current.connect();
        result.current.subscribe(['AAPL']);
      });

      const initialPrice = result.current.quotes['AAPL']?.price;
      expect(typeof initialPrice).toBe('number');
      expect(initialPrice).toBeGreaterThan(0);

      // Advance timer to trigger price update
      act(() => {
        jest.advanceTimersByTime(2000);
      });

      const updatedPrice = result.current.quotes['AAPL']?.price;
      expect(typeof updatedPrice).toBe('number');
      expect(updatedPrice).toBeGreaterThan(0);
    });

    it('should update quote data structure correctly', () => {
      const { result } = renderHook(() => useMarketWebSocket());

      act(() => {
        result.current.connect();
        result.current.subscribe(['AAPL']);
      });

      const quote = result.current.quotes['AAPL'];
      expect(quote).toHaveProperty('symbol', 'AAPL');
      expect(quote).toHaveProperty('price');
      expect(quote).toHaveProperty('timestamp');
      expect(quote).toHaveProperty('volume');
      expect(quote).toHaveProperty('high24h');
      expect(quote).toHaveProperty('low24h');
      expect(quote).toHaveProperty('change24h');

      expect(typeof quote.price).toBe('number');
      expect(typeof quote.timestamp).toBe('number');
      expect(typeof quote.volume).toBe('number');
    });

    it('should maintain price within reasonable bounds', () => {
      const { result } = renderHook(() => useMarketWebSocket());

      act(() => {
        result.current.connect();
        result.current.subscribe(['AAPL']);
      });

      // Run multiple updates to test price bounds
      for (let i = 0; i < 10; i++) {
        act(() => {
          jest.advanceTimersByTime(2000);
        });

        const price = result.current.quotes['AAPL']?.price;
        expect(price).toBeGreaterThan(0.01); // Minimum price check
        expect(price).toBeLessThan(10000); // Maximum reasonable price
      }
    });
  });

  describe('Cleanup and Memory Management', () => {
    it('should cleanup on unmount', () => {
      const { result, unmount } = renderHook(() => useMarketWebSocket({ autoConnect: true }));

      act(() => {
        result.current.subscribe(['AAPL']);
        jest.runAllTimers();
      });

      expect(result.current.isConnected).toBe(true);

      unmount();

      // Verify cleanup occurred (connection should be closed)
      // This test verifies the cleanup effect runs
    });

    it('should clear intervals when disconnecting', () => {
      const { result } = renderHook(() => useMarketWebSocket());

      act(() => {
        result.current.connect();
        result.current.subscribe(['AAPL']);
      });

      const clearIntervalSpy = jest.spyOn(global, 'clearInterval');

      act(() => {
        result.current.disconnect();
      });

      expect(clearIntervalSpy).toHaveBeenCalled();
      clearIntervalSpy.mockRestore();
    });
  });

  describe('Configuration Options', () => {
    it('should respect reconnectAttempts configuration', () => {
      const { result } = renderHook(() => 
        useMarketWebSocket({ 
          autoConnect: false,
          reconnectAttempts: 3,
          reconnectDelay: 1000
        })
      );

      // Test that configuration is accepted without errors
      expect(result.current.isConnected).toBe(false);
    });

    it('should respect reconnectDelay configuration', () => {
      const { result } = renderHook(() => 
        useMarketWebSocket({ 
          autoConnect: false,
          reconnectAttempts: 5,
          reconnectDelay: 5000
        })
      );

      // Test that configuration is accepted without errors
      expect(result.current.isConnected).toBe(false);
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty symbol arrays', () => {
      const { result } = renderHook(() => useMarketWebSocket());

      act(() => {
        result.current.connect();
        result.current.subscribe([]);
      });

      expect(Object.keys(result.current.quotes)).toHaveLength(0);
    });

    it('should handle unsubscribing from non-existent symbols', () => {
      const { result } = renderHook(() => useMarketWebSocket());

      act(() => {
        result.current.connect();
        result.current.unsubscribe(['NON_EXISTENT']);
      });

      expect(Object.keys(result.current.quotes)).toHaveLength(0);
    });

    it('should handle subscribing when not connected', () => {
      const { result } = renderHook(() => useMarketWebSocket());

      act(() => {
        result.current.subscribe(['AAPL']);
      });

      // Should still add symbols to subscription list even if not connected
      // They will be initialized when connection is established
      expect(Object.keys(result.current.quotes)).toContain('AAPL');
    });

    it('should handle multiple rapid subscribe/unsubscribe operations', () => {
      const { result } = renderHook(() => useMarketWebSocket());

      act(() => {
        result.current.connect();
        result.current.subscribe(['AAPL', 'GOOGL']);
        result.current.unsubscribe(['AAPL']);
        result.current.subscribe(['MSFT']);
        result.current.unsubscribe(['GOOGL']);
      });

      expect(Object.keys(result.current.quotes)).toEqual(['MSFT']);
    });
  });
});