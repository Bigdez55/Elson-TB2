/**
 * Test data factories for creating consistent test data
 * All factories allow partial overrides for flexibility
 */

import { User, Trade, Quote, Portfolio, Holding, Asset, TradingStats } from '../types';

// Counter for generating unique IDs
let idCounter = 1;
const generateId = () => idCounter++;

// Reset ID counter between test runs
export const resetIdCounter = () => {
  idCounter = 1;
};

/**
 * Create a test user
 */
export const createUser = (overrides?: Partial<User>): User => ({
  id: generateId(),
  email: `user${idCounter}@example.com`,
  full_name: `Test User ${idCounter}`,
  risk_tolerance: 'moderate',
  trading_style: 'long_term',
  is_active: true,
  is_verified: true,
  created_at: '2023-01-01T00:00:00Z',
  updated_at: new Date().toISOString(),
  ...overrides,
});

/**
 * Create a test trade
 */
export const createTrade = (overrides?: Partial<Trade>): Trade => ({
  id: generateId(),
  symbol: 'AAPL',
  trade_type: 'buy',
  order_type: 'market',
  quantity: 10,
  price: undefined,
  status: 'pending',
  created_at: new Date().toISOString(),
  executed_at: undefined,
  ...overrides,
});

/**
 * Create an executed trade
 */
export const createExecutedTrade = (overrides?: Partial<Trade>): Trade =>
  createTrade({
    status: 'executed',
    executed_at: new Date().toISOString(),
    executed_price: 150.0,
    ...overrides,
  });

/**
 * Create a test quote
 */
export const createQuote = (symbol: string = 'AAPL', overrides?: Partial<Quote>): Quote => ({
  symbol,
  open: 150.0,
  high: 155.0,
  low: 149.0,
  price: 152.5,
  volume: 10000000,
  change: 2.5,
  change_percent: 1.67,
  previous_close: 150.0,
  source: 'test',
  timestamp: new Date().toISOString(),
  ...overrides,
});

/**
 * Create multiple quotes for symbols
 */
export const createQuotes = (symbols: string[]): Quote[] =>
  symbols.map((symbol) => createQuote(symbol));

/**
 * Create a test portfolio
 */
export const createPortfolio = (overrides?: Partial<Portfolio>): Portfolio => ({
  id: generateId(),
  name: 'Test Portfolio',
  description: 'Test portfolio for unit tests',
  total_value: 100000.0,
  cash_balance: 25000.0,
  invested_amount: 75000.0,
  total_return: 5000.0,
  total_return_percentage: 5.26,
  auto_rebalance: false,
  is_active: true,
  created_at: '2023-01-01T00:00:00Z',
  updated_at: new Date().toISOString(),
  ...overrides,
});

/**
 * Create a test holding
 */
export const createHolding = (overrides?: Partial<Holding>): Holding => ({
  id: generateId(),
  symbol: 'AAPL',
  asset_type: 'stock',
  quantity: 50,
  average_cost: 140.0,
  current_price: 152.5,
  market_value: 7625.0,
  unrealized_gain_loss: 625.0,
  unrealized_gain_loss_percentage: 8.93,
  ...overrides,
});

/**
 * Create multiple holdings
 */
export const createHoldings = (count: number = 3): Holding[] => {
  const symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN'];
  return Array.from({ length: count }, (_, i) =>
    createHolding({
      symbol: symbols[i % symbols.length],
      quantity: (i + 1) * 10,
    })
  );
};

/**
 * Create a test asset
 */
export const createAsset = (overrides?: Partial<Asset>): Asset => ({
  id: generateId(),
  symbol: 'AAPL',
  name: 'Apple Inc.',
  asset_type: 'stock',
  exchange: 'NASDAQ',
  sector: 'Technology',
  industry: 'Consumer Electronics',
  is_tradable: true,
  ...overrides,
});

/**
 * Create test trading stats
 */
export const createTradingStats = (overrides?: Partial<TradingStats>): TradingStats => ({
  total_trades: 50,
  winning_trades: 30,
  losing_trades: 20,
  win_rate: 0.6,
  total_profit_loss: 2500.0,
  average_profit_loss: 125.0,
  largest_win: 500.0,
  largest_loss: -200.0,
  total_commission: 50.0,
  ...overrides,
});

/**
 * Create auth state for preloaded store state
 */
export const createAuthState = (overrides?: Partial<{
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
}>) => ({
  user: createUser(),
  token: 'test-token-123',
  loading: false,
  error: null,
  ...overrides,
});

/**
 * Create trading state for preloaded store state
 */
export const createTradingState = (overrides?: Partial<{
  mode: 'paper' | 'live';
  openOrders: Trade[];
  tradeHistory: Trade[];
  loading: boolean;
  error: string | null;
}>) => ({
  mode: 'paper' as const,
  openOrders: [],
  tradeHistory: [],
  loading: false,
  error: null,
  ...overrides,
});

/**
 * Create portfolio state for preloaded store state
 */
export const createPortfolioState = (overrides?: Partial<{
  portfolio: Portfolio | null;
  holdings: Holding[];
  loading: boolean;
  error: string | null;
}>) => ({
  portfolio: createPortfolio(),
  holdings: createHoldings(3),
  loading: false,
  error: null,
  ...overrides,
});

/**
 * Create websocket state for preloaded store state
 */
export const createWebsocketState = (overrides?: Partial<{
  status: string;
  lastConnected: Date | null;
  reconnectAttempts: number;
  marketData: Record<string, any>;
  portfolio: { paper: any; live: any };
  positions: Record<string, any>;
  recentOrders: any[];
  subscribedChannels: string[];
  messageCount: number;
  lastMessageTime: Date | null;
  error: string | null;
}>) => ({
  status: 'DISCONNECTED',
  lastConnected: null,
  reconnectAttempts: 0,
  marketData: {},
  portfolio: { paper: null, live: null },
  positions: {},
  recentOrders: [],
  subscribedChannels: [],
  messageCount: 0,
  lastMessageTime: null,
  error: null,
  ...overrides,
});

/**
 * Create a full preloaded state for tests
 */
export const createPreloadedState = (overrides?: Partial<{
  auth: ReturnType<typeof createAuthState>;
  trading: ReturnType<typeof createTradingState>;
  portfolio: ReturnType<typeof createPortfolioState>;
  websocket: ReturnType<typeof createWebsocketState>;
}>) => ({
  auth: createAuthState(),
  trading: createTradingState(),
  portfolio: createPortfolioState(),
  websocket: createWebsocketState(),
  marketData: {
    quotes: {},
    assets: [],
    loading: false,
    error: null,
  },
  ...overrides,
});
