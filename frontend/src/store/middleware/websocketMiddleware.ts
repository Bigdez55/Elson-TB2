import { Middleware, AnyAction } from '@reduxjs/toolkit';
import { webSocketService } from '../../services/websocketService';
import {
  setConnectionStatus,
  updateMarketData,
  addOrderUpdate,
  updatePosition,
  updatePortfolio,
  addSubscription,
  removeSubscription,
  incrementMessageCount,
} from '../slices/websocketSlice';
import { marketDataApi } from '../../services/marketDataApi';
import { tradingApi } from '../../services/tradingApi';
import { riskManagementApi } from '../../services/riskManagementApi';
import type { RootState } from '../store';

// WebSocket middleware for Redux integration
export const websocketMiddleware: Middleware<{}, RootState> = (store) => (next) => (action) => {
  const result = next(action);

  // Type guard for action
  const typedAction = action as AnyAction;

  // Handle specific Redux actions that should trigger WebSocket operations
  if (typedAction.type === 'websocket/connectWebSocket') {
    handleWebSocketConnection(store);
  } else if (typedAction.type === 'websocket/disconnectWebSocket') {
    handleWebSocketDisconnection(store);
  } else if (typedAction.type?.startsWith('tradingApi/executeTrade/fulfilled')) {
    // Invalidate cache and request real-time updates after successful trade
    handleTradeExecuted(store, typedAction);
  } else if (typedAction.type?.startsWith('marketDataApi/')) {
    // Handle market data API calls
    handleMarketDataRequest(store, typedAction);
  }

  return result;
};

const handleWebSocketConnection = async (store: any) => {
  try {
    // Set up event handlers before connecting
    webSocketService.on('onStatusChange', (status: any) => {
      store.dispatch(setConnectionStatus({
        status,
        lastConnected: new Date(),
        reconnectAttempts: 0,
      }));
    });

    webSocketService.on('onError', (error: any) => {
      store.dispatch(setConnectionStatus({
        status: webSocketService.getState().status,
        error,
      }));
    });

    webSocketService.on('onMarketData', (data: any) => {
      store.dispatch(updateMarketData(data));
      store.dispatch(incrementMessageCount());
      
      // Update market data cache
      store.dispatch(marketDataApi.util.updateQueryData(
        'getQuote',
        data.symbol,
        (draft) => {
          if (draft) {
            draft.price = data.price;
            draft.change = data.change;
            draft.change_percent = data.change_percent;
            draft.volume = data.volume;
            draft.timestamp = data.timestamp;
          }
        }
      ));
    });

    webSocketService.on('onOrderUpdate', (data: any) => {
      store.dispatch(addOrderUpdate(data));
      store.dispatch(incrementMessageCount());
      
      // Invalidate relevant trading queries
      const mode = data.paper_trading ? 'paper' : 'live';
      store.dispatch(tradingApi.util.invalidateTags([
        { type: 'OrderHistory', id: `${mode}_data` },
        { type: 'Portfolio', id: `${mode}_data` },
      ]));
    });

    webSocketService.on('onPositionUpdate', (data: any) => {
      store.dispatch(updatePosition(data));
      store.dispatch(incrementMessageCount());
      
      // Update position cache
      const mode = data.paper_trading ? 'paper' : 'live';
      store.dispatch(tradingApi.util.invalidateTags([
        { type: 'Position', id: `${mode}_data` },
        { type: 'Portfolio', id: `${mode}_data` },
      ]));
    });

    webSocketService.on('onPortfolioUpdate', (data: any) => {
      store.dispatch(updatePortfolio(data));
      store.dispatch(incrementMessageCount());
      
      // Update portfolio cache
      const mode = data.paper_trading ? 'paper' : 'live';
      store.dispatch(tradingApi.util.updateQueryData(
        'getPortfolio',
        { mode },
        (draft) => {
          if (draft) {
            draft.total_value = data.total_value;
            draft.cash_balance = data.cash_balance;
            draft.day_pnl = data.day_pnl;
            draft.day_pnl_percent = data.day_pnl_percent;
            draft.last_updated = data.timestamp;
          }
        }
      ));
    });

    // Connect to WebSocket
    await webSocketService.connect();

    // Subscribe to default channels based on current state
    const state = store.getState();
    await setupDefaultSubscriptions(store, state);

  } catch (error) {
    console.error('WebSocket connection failed:', error);
    const state = webSocketService.getState?.() ?? { status: 'ERROR' };
    store.dispatch(setConnectionStatus({
      status: state.status ?? 'ERROR',
      error: error instanceof Error ? error.message : 'Connection failed',
    }));
  }
};

const handleWebSocketDisconnection = (store: any) => {
  webSocketService.disconnect();

  // Clear all event handlers
  webSocketService.off('onStatusChange');
  webSocketService.off('onError');
  webSocketService.off('onMarketData');
  webSocketService.off('onOrderUpdate');
  webSocketService.off('onPositionUpdate');
  webSocketService.off('onPortfolioUpdate');

  const state = webSocketService.getState?.() ?? { status: 'DISCONNECTED' };
  store.dispatch(setConnectionStatus({
    status: state.status ?? 'DISCONNECTED',
  }));
};

const setupDefaultSubscriptions = async (store: any, state: RootState) => {
  try {
    // Subscribe to portfolio updates for current trading mode
    const tradingMode = localStorage.getItem('tradingMode') || 'paper';
    await webSocketService.subscribeToPortfolio(tradingMode as 'paper' | 'live');
    await webSocketService.subscribeToOrderUpdates(tradingMode as 'paper' | 'live');
    
    store.dispatch(addSubscription(`portfolio:${tradingMode}`));
    store.dispatch(addSubscription(`orders:${tradingMode}`));

    // Subscribe to market data for any symbols currently being viewed
    const marketDataQueries = state.marketDataApi?.queries || {};
    const symbolsToSubscribe: string[] = [];
    
    Object.keys(marketDataQueries).forEach(queryKey => {
      if (queryKey.includes('getQuote')) {
        const query = marketDataQueries[queryKey];
        if (query?.data && (query.data as any).symbol) {
          symbolsToSubscribe.push((query.data as any).symbol);
        }
      }
    });

    if (symbolsToSubscribe.length > 0) {
      await webSocketService.subscribeToMarketData(symbolsToSubscribe);
      store.dispatch(addSubscription(`market_data:${symbolsToSubscribe.join(',')}`));
    }

  } catch (error) {
    console.error('Failed to set up default subscriptions:', error);
  }
};

const handleTradeExecuted = async (store: any, action: any) => {
  const { mode } = action.meta.arg;
  
  // Invalidate all trading-related queries for the specific mode
  store.dispatch(tradingApi.util.invalidateTags([
    { type: 'Portfolio', id: `${mode}_data` },
    { type: 'Position', id: `${mode}_data` },
    { type: 'OrderHistory', id: `${mode}_data` },
    { type: 'TradingAccount', id: `${mode}_data` },
  ]));

  // Also invalidate risk management queries
  store.dispatch(riskManagementApi.util.invalidateTags([
    'RiskMetrics',
    'PositionRisk',
  ]));

  // Subscribe to updates for the traded symbol if not already subscribed
  const symbol = action.meta.arg.symbol;
  const state = store.getState();
  const subscribedChannels = state.websocket.subscribedChannels;
  
  const marketDataChannel = `market_data:${symbol}`;
  const isAlreadySubscribed = subscribedChannels.some((channel: string) => 
    channel.includes('market_data') && channel.includes(symbol)
  );

  if (!isAlreadySubscribed && webSocketService.isConnected()) {
    try {
      await webSocketService.subscribeToMarketData([symbol]);
      store.dispatch(addSubscription(marketDataChannel));
    } catch (error) {
      console.error('Failed to subscribe to market data after trade:', error);
    }
  }
};

const handleMarketDataRequest = async (store: any, action: any) => {
  // Auto-subscribe to real-time data when market data is requested
  if (action.type.includes('getQuote/pending')) {
    const symbol = action.meta.arg.symbol;
    const state = store.getState();
    const subscribedChannels = state.websocket.subscribedChannels;
    
    const marketDataChannel = `market_data:${symbol}`;
    const isAlreadySubscribed = subscribedChannels.some((channel: string) => 
      channel.includes('market_data') && channel.includes(symbol)
    );

    if (!isAlreadySubscribed && webSocketService.isConnected()) {
      try {
        await webSocketService.subscribeToMarketData([symbol]);
        store.dispatch(addSubscription(marketDataChannel));
      } catch (error) {
        console.error('Failed to auto-subscribe to market data:', error);
      }
    }
  }
};

// Enhanced middleware with automatic symbol tracking
const enhancedMiddleware = (store: any) => (next: any) => (action: any) => {
  const result = next(action);
  
  // Handle base WebSocket actions
  if (action.type === 'websocket/connectWebSocket') {
    handleWebSocketConnection(store);
  } else if (action.type === 'websocket/disconnectWebSocket') {
    handleWebSocketDisconnection(store);
  } else if (action.type?.startsWith('tradingApi/executeTrade/fulfilled')) {
    handleTradeExecuted(store, action);
  } else if (action.type?.startsWith('marketDataApi/')) {
    handleMarketDataRequest(store, action);
  }
  
  // Handle enhanced features
  if (action.type === '@@router/LOCATION_CHANGE' || action.payload?.pathname) {
    const pathname = action.payload?.pathname || window.location.pathname;
    const tradingMatch = pathname.match(/\/(?:paper|live)\/trading\/([A-Z]+)/);
    
    if (tradingMatch) {
      const symbol = tradingMatch[1];
      handleSymbolNavigation(store, symbol);
    }
  }
  
  // Handle trading mode changes
  if (action.type === 'trading/setMode' || action.payload?.mode) {
    const newMode = action.payload?.mode;
    if (newMode) {
      handleTradingModeChange(store, newMode);
    }
  }

  return result;
};

export const enhancedWebsocketMiddleware = enhancedMiddleware;

const handleSymbolNavigation = async (store: any, symbol: string) => {
  if (!webSocketService.isConnected()) return;

  const state = store.getState();
  const subscribedChannels = state.websocket.subscribedChannels;
  
  const marketDataChannel = `market_data:${symbol}`;
  const isAlreadySubscribed = subscribedChannels.some((channel: string) => 
    channel.includes('market_data') && channel.includes(symbol)
  );

  if (!isAlreadySubscribed) {
    try {
      await webSocketService.subscribeToMarketData([symbol]);
      store.dispatch(addSubscription(marketDataChannel));
    } catch (error) {
      console.error('Failed to subscribe to market data on navigation:', error);
    }
  }
};

const handleTradingModeChange = async (store: any, newMode: 'paper' | 'live') => {
  if (!webSocketService.isConnected()) return;

  try {
    // Unsubscribe from old mode channels
    const state = store.getState();
    const oldModeChannels = state.websocket.subscribedChannels.filter((channel: string) =>
      channel.includes('portfolio:') || channel.includes('orders:')
    );

    for (const channel of oldModeChannels) {
      await webSocketService.unsubscribe(channel);
      store.dispatch(removeSubscription(channel));
    }

    // Subscribe to new mode channels
    await webSocketService.subscribeToPortfolio(newMode);
    await webSocketService.subscribeToOrderUpdates(newMode);
    
    store.dispatch(addSubscription(`portfolio:${newMode}`));
    store.dispatch(addSubscription(`orders:${newMode}`));

  } catch (error) {
    console.error('Failed to handle trading mode change:', error);
  }
};

export default enhancedWebsocketMiddleware;