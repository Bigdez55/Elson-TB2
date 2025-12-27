import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { 
  WebSocketStatus, 
  MarketDataUpdate, 
  OrderUpdate, 
  PositionUpdate, 
  PortfolioUpdate 
} from '../../services/websocketService';

// WebSocket Redux State
export interface WebSocketState {
  status: WebSocketStatus;
  lastConnected: string | null; // ISO string for serialization
  reconnectAttempts: number;
  error: string | null;
  
  // Real-time data
  marketData: Record<string, MarketDataUpdate>;
  recentOrders: OrderUpdate[];
  positions: Record<string, PositionUpdate>;
  portfolio: {
    paper: PortfolioUpdate | null;
    live: PortfolioUpdate | null;
  };
  
  // Connection metrics
  messageCount: number;
  lastMessageTime: string | null;
  
  // Subscriptions
  subscribedChannels: string[];
}

const initialState: WebSocketState = {
  status: WebSocketStatus.DISCONNECTED,
  lastConnected: null,
  reconnectAttempts: 0,
  error: null,
  
  marketData: {},
  recentOrders: [],
  positions: {},
  portfolio: {
    paper: null,
    live: null,
  },
  
  messageCount: 0,
  lastMessageTime: null,
  
  subscribedChannels: [],
};

const websocketSlice = createSlice({
  name: 'websocket',
  initialState,
  reducers: {
    // Connection management
    setConnectionStatus: (state, action: PayloadAction<{
      status: WebSocketStatus;
      lastConnected?: Date;
      reconnectAttempts?: number;
      error?: string | null;
    }>) => {
      state.status = action.payload.status;
      
      if (action.payload.lastConnected) {
        state.lastConnected = action.payload.lastConnected.toISOString();
      }
      
      if (typeof action.payload.reconnectAttempts === 'number') {
        state.reconnectAttempts = action.payload.reconnectAttempts;
      }
      
      if (action.payload.error !== undefined) {
        state.error = action.payload.error;
      }
    },

    clearError: (state) => {
      state.error = null;
    },

    incrementMessageCount: (state) => {
      state.messageCount += 1;
      state.lastMessageTime = new Date().toISOString();
    },

    // Market data updates
    updateMarketData: (state, action: PayloadAction<MarketDataUpdate>) => {
      const data = action.payload;
      state.marketData[data.symbol] = data;
      websocketSlice.caseReducers.incrementMessageCount(state);
    },

    clearMarketData: (state, action: PayloadAction<string[]>) => {
      action.payload.forEach(symbol => {
        delete state.marketData[symbol];
      });
    },

    // Order updates
    addOrderUpdate: (state, action: PayloadAction<OrderUpdate>) => {
      const orderUpdate = action.payload;
      
      // Add to recent orders (keep last 50)
      state.recentOrders.unshift(orderUpdate);
      state.recentOrders = state.recentOrders.slice(0, 50);
      
      websocketSlice.caseReducers.incrementMessageCount(state);
    },

    clearOrderHistory: (state) => {
      state.recentOrders = [];
    },

    // Position updates
    updatePosition: (state, action: PayloadAction<PositionUpdate>) => {
      const position = action.payload;
      const key = `${position.symbol}_${position.paper_trading ? 'paper' : 'live'}`;
      
      if (position.quantity === 0) {
        // Position closed
        delete state.positions[key];
      } else {
        state.positions[key] = position;
      }
      
      websocketSlice.caseReducers.incrementMessageCount(state);
    },

    // Portfolio updates
    updatePortfolio: (state, action: PayloadAction<PortfolioUpdate>) => {
      const portfolio = action.payload;
      const mode = portfolio.paper_trading ? 'paper' : 'live';
      state.portfolio[mode] = portfolio;
      
      websocketSlice.caseReducers.incrementMessageCount(state);
    },

    // Subscription management
    addSubscription: (state, action: PayloadAction<string>) => {
      const channel = action.payload;
      if (!state.subscribedChannels.includes(channel)) {
        state.subscribedChannels.push(channel);
      }
    },

    removeSubscription: (state, action: PayloadAction<string>) => {
      const channel = action.payload;
      state.subscribedChannels = state.subscribedChannels.filter(ch => ch !== channel);
    },

    clearSubscriptions: (state) => {
      state.subscribedChannels = [];
    },

    // Bulk operations for performance
    bulkUpdateMarketData: (state, action: PayloadAction<MarketDataUpdate[]>) => {
      action.payload.forEach(data => {
        state.marketData[data.symbol] = data;
      });
      state.messageCount += action.payload.length;
      state.lastMessageTime = new Date().toISOString();
    },

    // Reset all real-time data (useful on disconnect)
    resetRealtimeData: (state) => {
      state.marketData = {};
      state.recentOrders = [];
      state.positions = {};
      state.portfolio = { paper: null, live: null };
      state.messageCount = 0;
      state.lastMessageTime = null;
    },

    // Complete reset
    resetWebSocketState: () => initialState,
  },
});

// Exported actions
export const {
  setConnectionStatus,
  clearError,
  incrementMessageCount,
  updateMarketData,
  clearMarketData,
  addOrderUpdate,
  clearOrderHistory,
  updatePosition,
  updatePortfolio,
  addSubscription,
  removeSubscription,
  clearSubscriptions,
  bulkUpdateMarketData,
  resetRealtimeData,
  resetWebSocketState,
} = websocketSlice.actions;

// Selectors
export const selectWebSocketStatus = (state: { websocket: WebSocketState }) => 
  state.websocket.status;

export const selectIsConnected = (state: { websocket: WebSocketState }) =>
  state.websocket.status === WebSocketStatus.AUTHENTICATED;

export const selectConnectionError = (state: { websocket: WebSocketState }) =>
  state.websocket.error;

export const selectMarketData = (state: { websocket: WebSocketState }) =>
  state.websocket.marketData;

export const selectSymbolPrice = (symbol: string) => (state: { websocket: WebSocketState }) =>
  state.websocket.marketData[symbol]?.price;

export const selectRecentOrders = (state: { websocket: WebSocketState }) =>
  state.websocket.recentOrders;

export const selectPositions = (mode: 'paper' | 'live') => (state: { websocket: WebSocketState }) =>
  Object.values(state.websocket.positions).filter(
    position => position.paper_trading === (mode === 'paper')
  );

export const selectPortfolio = (mode: 'paper' | 'live') => (state: { websocket: WebSocketState }) =>
  state.websocket.portfolio[mode];

export const selectConnectionMetrics = (state: { websocket: WebSocketState }) => ({
  status: state.websocket.status,
  lastConnected: state.websocket.lastConnected,
  reconnectAttempts: state.websocket.reconnectAttempts,
  messageCount: state.websocket.messageCount,
  lastMessageTime: state.websocket.lastMessageTime,
  subscribedChannels: state.websocket.subscribedChannels,
});

// Async thunks for WebSocket operations
export const connectWebSocket = () => async (dispatch: any) => {
  try {
    dispatch(setConnectionStatus({ status: WebSocketStatus.CONNECTING }));
    
    const { webSocketService } = await import('../../services/websocketService');
    await webSocketService.connect();
    
    // Connection status will be updated by the WebSocket event handlers
  } catch (error) {
    dispatch(setConnectionStatus({
      status: WebSocketStatus.ERROR,
      error: error instanceof Error ? error.message : 'Connection failed',
    }));
    throw error;
  }
};

export const disconnectWebSocket = () => async (dispatch: any) => {
  try {
    const { webSocketService } = await import('../../services/websocketService');
    webSocketService.disconnect();
    
    dispatch(resetRealtimeData());
    dispatch(clearSubscriptions());
    dispatch(setConnectionStatus({ status: WebSocketStatus.DISCONNECTED }));
  } catch (error) {
    console.error('Error during WebSocket disconnect:', error);
  }
};

export const subscribeToChannel = (channel: string) => async (dispatch: any) => {
  try {
    const { webSocketService } = await import('../../services/websocketService');
    await webSocketService.subscribe(channel);
    
    dispatch(addSubscription(channel));
  } catch (error) {
    console.error('Subscription failed:', error);
    throw error;
  }
};

export const unsubscribeFromChannel = (channel: string) => async (dispatch: any) => {
  try {
    const { webSocketService } = await import('../../services/websocketService');
    await webSocketService.unsubscribe(channel);
    
    dispatch(removeSubscription(channel));
  } catch (error) {
    console.error('Unsubscription failed:', error);
    throw error;
  }
};

export { websocketSlice };
export default websocketSlice.reducer;