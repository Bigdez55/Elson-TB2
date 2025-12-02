// frontend/src/types/index.ts

export interface MarketData {
  symbol: string;
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  indicators: TechnicalIndicators;
}

export interface TechnicalIndicators {
  sma20: number;
  sma50: number;
  rsi: number;
  macd: {
    line: number;
    signal: number;
    histogram: number;
  };
  bollingerBands: {
    upper: number;
    middle: number;
    lower: number;
  };
}

export interface PredictionData {
  symbol: string;
  timestamp: number;
  predictedPrice: number;
  confidence: number;
  range: {
    upper: number;
    lower: number;
  };
  timeframe: TimeFrame;
  signals: Signal[];
}

export type TimeFrame = 'short_term' | 'medium_term' | 'long_term';

export interface Signal {
  type: 'BUY' | 'SELL';
  strength: number;
  reason: string;
}

export interface Position {
  id: string;
  symbol: string;
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  unrealizedPnL: number;
  realizedPnL: number;
  stopLoss?: number;
  takeProfit?: number;
  timestamp: number;
}

export interface Order {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  type: OrderType;
  quantity: number;
  price?: number;
  stopPrice?: number;
  status: OrderStatus;
  timestamp: number;
}

export type OrderType = 'MARKET' | 'LIMIT' | 'STOP' | 'STOP_LIMIT';
export type OrderStatus = 'NEW' | 'FILLED' | 'PARTIALLY_FILLED' | 'CANCELED' | 'REJECTED';

export interface TradeSignal {
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  confidence: number;
  timestamp: number;
  predictedRange: {
    upper: number;
    lower: number;
    timeframe: TimeFrame;
  };
  indicators: TechnicalIndicators;
  sentiment: SentimentData;
}

export interface SentimentData {
  score: number;
  magnitude: number;
  sources: {
    news: number;
    social: number;
    technical: number;
  };
}

export interface Performance {
  totalValue: number;
  dailyPnL: number;
  totalPnL: number;
  winRate: number;
  sharpeRatio: number;
  metrics: RiskMetrics;
  history: PerformanceHistory[];
}

export interface RiskMetrics {
  valueAtRisk: number;
  expectedShortfall: number;
  maxDrawdown: number;
  beta: number;
  sortinoRatio: number;
  informationRatio: number;
  treynorRatio: number;
  correlationMatrix: number[][];
}

export interface PerformanceHistory {
  timestamp: number;
  portfolioValue: number;
  dailyReturn: number;
  benchmarkValue: number;
  benchmarkReturn: number;
}

export interface TradeValidation {
  isValid: boolean;
  reasons?: string[];
  suggestedSize?: number;
  riskAssessment: {
    positionRisk: number;
    portfolioRisk: number;
    maxLoss: number;
  };
}

export interface OrderRequest {
  symbol: string;
  side: 'BUY' | 'SELL';
  type: OrderType;
  quantity: number;
  price?: number;
  stopPrice?: number;
  timeInForce?: TimeInForce;
  clientOrderId?: string;
}

export type TimeInForce = 'GTC' | 'IOC' | 'FOK' | 'DAY';

export interface Alert {
  id: string;
  type: 'success' | 'warning' | 'error' | 'info';
  title: string;
  message: string;
  timestamp: number;
  isRead: boolean;
}

export interface ModelMetrics {
  name: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1Score: number;
  confusionMatrix: number[][];
  predictionHistory: PredictionHistoryEntry[];
}

export interface PredictionHistoryEntry {
  timestamp: number;
  predicted: number;
  actual: number;
  error: number;
  confidence: number;
}

export interface BacktestResult {
  startDate: number;
  endDate: number;
  totalReturn: number;
  annualizedReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  trades: BacktestTrade[];
  equityCurve: EquityPoint[];
}

export interface BacktestTrade {
  symbol: string;
  entryTime: number;
  exitTime: number;
  entryPrice: number;
  exitPrice: number;
  quantity: number;
  pnl: number;
  side: 'BUY' | 'SELL';
}

export interface EquityPoint {
  timestamp: number;
  value: number;
  drawdown: number;
  return: number;
}

export interface MarketEnvironment {
  regime: 'BULL' | 'BEAR' | 'SIDEWAYS';
  volatility: number;
  trend: {
    strength: number;
    direction: 'UP' | 'DOWN' | 'NEUTRAL';
  };
  liquidity: number;
  correlations: {
    spy: number;
    qqq: number;
    vix: number;
  };
}

export interface RiskProfile {
  maxPositionSize: number;
  maxDrawdown: number;
  riskPerTrade: number;
  targetVolatility: number;
  rebalanceThreshold: number;
  stopLossSettings: {
    enabled: boolean;
    type: 'FIXED' | 'TRAILING' | 'ATR';
    value: number;
  };
}

export interface WebSocketMessage {
  type: WebSocketMessageType;
  data: any;
  timestamp: number;
}

export type WebSocketMessageType = 
  | 'MARKET_DATA'
  | 'TRADE'
  | 'PREDICTION'
  | 'SIGNAL'
  | 'ERROR'
  | 'AUTH'
  | 'HEARTBEAT';

export interface APIError {
  code: string;
  message: string;
  details?: Record<string, any>;
}

export interface RecurringInvestment {
  id: number;
  user_id: number;
  portfolio_id: number;
  symbol: string;
  investment_amount: number;
  frequency: string;
  start_date: string;
  end_date?: string;
  next_investment_date: string;
  last_execution_date?: string;
  is_active: boolean;
  execution_count: number;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface RoundupTransaction {
  id: number;
  user_id: number;
  transaction_amount: number;
  roundup_amount: number;
  transaction_date: string;
  description: string | null;
  source: string | null;
  status: string; // 'pending', 'invested', 'cancelled'
  invested_at: string | null;
  trade_id: number | null;
}

export interface RoundupSummary {
  total_roundups: number;
  total_amount: number;
  pending_amount: number;
  invested_amount: number;
  total_investments: number;
  last_investment_date: string | null;
}