/**
 * WebSocket testing utilities
 * Provides mock WebSocket functionality for testing real-time features
 */

type MessageHandler = (data: any) => void;
type EventHandler = () => void;

/**
 * Mock WebSocket class for testing
 * Simulates WebSocket behavior without actual network connections
 */
export class MockWebSocket {
  static readonly CONNECTING = 0;
  static readonly OPEN = 1;
  static readonly CLOSING = 2;
  static readonly CLOSED = 3;

  url: string;
  readyState: number = MockWebSocket.CONNECTING;

  onopen: EventHandler | null = null;
  onclose: EventHandler | null = null;
  onerror: ((event: { message: string }) => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;

  private messageQueue: any[] = [];
  private isOpen = false;

  constructor(url: string) {
    this.url = url;
    // Simulate connection delay
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      this.isOpen = true;
      this.onopen?.();
      // Send queued messages
      this.messageQueue.forEach((msg) => this.send(msg));
      this.messageQueue = [];
    }, 10);
  }

  send(data: string | object) {
    if (!this.isOpen) {
      this.messageQueue.push(data);
      return;
    }
    const message = typeof data === 'string' ? data : JSON.stringify(data);
    // Simulate server echo or response (for testing)
    MockWebSocketServer.handleMessage(this, message);
  }

  close() {
    this.readyState = MockWebSocket.CLOSING;
    setTimeout(() => {
      this.readyState = MockWebSocket.CLOSED;
      this.isOpen = false;
      this.onclose?.();
    }, 10);
  }

  // Test helper to simulate receiving a message
  simulateMessage(data: any) {
    const message = typeof data === 'string' ? data : JSON.stringify(data);
    this.onmessage?.({ data: message });
  }

  // Test helper to simulate error
  simulateError(message: string) {
    this.onerror?.({ message });
  }

  // Test helper to simulate close
  simulateClose() {
    this.readyState = MockWebSocket.CLOSED;
    this.isOpen = false;
    this.onclose?.();
  }
}

/**
 * Mock WebSocket Server for testing
 * Manages all mock WebSocket connections and can broadcast messages
 */
export class MockWebSocketServer {
  private static connections: MockWebSocket[] = [];
  private static messageHandlers: Map<string, MessageHandler> = new Map();

  /**
   * Register a new connection
   */
  static addConnection(ws: MockWebSocket) {
    this.connections.push(ws);
  }

  /**
   * Remove a connection
   */
  static removeConnection(ws: MockWebSocket) {
    const index = this.connections.indexOf(ws);
    if (index > -1) {
      this.connections.splice(index, 1);
    }
  }

  /**
   * Handle incoming message from client
   */
  static handleMessage(ws: MockWebSocket, message: string) {
    try {
      const data = JSON.parse(message);
      const handler = this.messageHandlers.get(data.type);
      if (handler) {
        handler(data);
      }
    } catch {
      // Non-JSON message, ignore
    }
  }

  /**
   * Register a handler for a specific message type
   */
  static onMessage(type: string, handler: MessageHandler) {
    this.messageHandlers.set(type, handler);
  }

  /**
   * Broadcast message to all connections
   */
  static broadcast(data: any) {
    const message = typeof data === 'string' ? data : JSON.stringify(data);
    this.connections.forEach((ws) => {
      if (ws.readyState === MockWebSocket.OPEN) {
        ws.onmessage?.({ data: message });
      }
    });
  }

  /**
   * Send message to specific connection
   */
  static sendTo(ws: MockWebSocket, data: any) {
    const message = typeof data === 'string' ? data : JSON.stringify(data);
    ws.onmessage?.({ data: message });
  }

  /**
   * Simulate a market data update
   */
  static sendMarketData(data: {
    symbol: string;
    price: number;
    change?: number;
    change_percent?: number;
    volume?: number;
  }) {
    this.broadcast({
      type: 'market_data',
      data: {
        timestamp: new Date().toISOString(),
        ...data,
      },
    });
  }

  /**
   * Simulate an order update
   */
  static sendOrderUpdate(data: {
    order_id: number;
    status: string;
    symbol: string;
    filled_qty?: number;
    filled_price?: number;
  }) {
    this.broadcast({
      type: 'order_update',
      data: {
        timestamp: new Date().toISOString(),
        ...data,
      },
    });
  }

  /**
   * Simulate a portfolio update
   */
  static sendPortfolioUpdate(data: {
    total_value: number;
    cash_balance: number;
    day_pnl?: number;
    day_pnl_percent?: number;
  }) {
    this.broadcast({
      type: 'portfolio_update',
      data: {
        timestamp: new Date().toISOString(),
        ...data,
      },
    });
  }

  /**
   * Simulate a position update
   */
  static sendPositionUpdate(data: {
    symbol: string;
    quantity: number;
    market_value: number;
    unrealized_pnl: number;
  }) {
    this.broadcast({
      type: 'position_update',
      data: {
        timestamp: new Date().toISOString(),
        ...data,
      },
    });
  }

  /**
   * Simulate heartbeat pong
   */
  static sendPong() {
    this.broadcast({ type: 'pong' });
  }

  /**
   * Reset all state
   */
  static reset() {
    this.connections = [];
    this.messageHandlers.clear();
  }
}

/**
 * Install mock WebSocket globally
 * Call this in beforeEach/beforeAll to replace global WebSocket
 */
export const installMockWebSocket = () => {
  (global as any).WebSocket = MockWebSocket;
};

/**
 * Restore original WebSocket
 * Call this in afterEach/afterAll to restore original WebSocket
 */
export const restoreMockWebSocket = () => {
  delete (global as any).WebSocket;
};

/**
 * Wait for WebSocket to connect
 */
export const waitForConnection = (ws: MockWebSocket): Promise<void> => {
  return new Promise((resolve) => {
    if (ws.readyState === MockWebSocket.OPEN) {
      resolve();
    } else {
      const originalOnOpen = ws.onopen;
      ws.onopen = () => {
        originalOnOpen?.();
        resolve();
      };
    }
  });
};

/**
 * Wait for a specific message type
 */
export const waitForMessage = (
  ws: MockWebSocket,
  messageType: string,
  timeout = 1000
): Promise<any> => {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(new Error(`Timeout waiting for message type: ${messageType}`));
    }, timeout);

    const originalOnMessage = ws.onmessage;
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === messageType) {
          clearTimeout(timer);
          ws.onmessage = originalOnMessage;
          resolve(data);
        } else {
          originalOnMessage?.(event);
        }
      } catch {
        originalOnMessage?.(event);
      }
    };
  });
};
