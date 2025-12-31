import api from './api';
import type { RoundupTransaction, RoundupSummary } from '../types';

interface RoundupTransactionParams {
  page?: number;
  limit?: number;
  offset?: number;
  status?: string;
  start_date?: string;
  end_date?: string;
  startDate?: string;
  endDate?: string;
}

interface RoundupTransactionResponse {
  transactions: RoundupTransaction[];
  total: number;
  pending_total: number;
  invested_total: number;
}

interface SymbolInfo {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap?: number;
  exchange?: string;
}

interface OrderData {
  symbol: string;
  quantity?: number;
  amount?: number;
  investment_amount?: number;
  side?: 'buy' | 'sell';
  order_type?: 'market' | 'limit' | 'stop' | 'stop_limit';
  time_in_force?: 'day' | 'gtc' | 'ioc' | 'fok';
  limit_price?: number;
  stop_price?: number;
  trade_type?: string;
  portfolio_id?: string;
  investment_type?: string;
  is_fractional?: boolean;
}

interface RecurringInvestmentCreate {
  symbol: string;
  amount?: number;
  investment_amount?: number;
  frequency: string;
  day_of_week?: number;
  day_of_month?: number;
  start_date?: string;
  portfolio_id?: string;
  trade_type?: string;
}

interface RecurringInvestment {
  id?: number;
  symbol: string;
  amount: number;
  frequency: 'daily' | 'weekly' | 'biweekly' | 'monthly';
  day_of_week?: number;
  day_of_month?: number;
  next_execution_date?: string;
  status?: 'active' | 'paused' | 'cancelled';
  created_at?: string;
}

interface OrderResult {
  id: number;
  symbol: string;
  quantity: number;
  filled_quantity: number;
  price: number;
  status: string;
  order_type: string;
  side: string;
  created_at: string;
}

export const tradingService = {
  // Roundup transaction methods
  async getRoundupTransactions(
    params: RoundupTransactionParams = {},
    _includeStats: boolean = false
  ): Promise<RoundupTransactionResponse> {
    const queryParams = new URLSearchParams();
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.limit) queryParams.append('limit', params.limit.toString());
    if (params.offset !== undefined) queryParams.append('offset', params.offset.toString());
    if (params.status) queryParams.append('status', params.status);
    // Support both naming conventions
    const startDate = params.start_date || params.startDate;
    const endDate = params.end_date || params.endDate;
    if (startDate) queryParams.append('start_date', startDate);
    if (endDate) queryParams.append('end_date', endDate);

    const response = await api.get(`/roundup/transactions?${queryParams.toString()}`);
    return response.data;
  },

  async investPendingRoundups(): Promise<{ message: string; invested_amount: number }> {
    const response = await api.post('/roundup/invest');
    return response.data;
  },

  async getRoundupSummary(_includeDetails: boolean = false): Promise<RoundupSummary> {
    const response = await api.get('/roundup/summary');
    return response.data;
  },

  // Symbol info methods
  async getSymbolInfo(symbol: string): Promise<SymbolInfo> {
    const response = await api.get(`/market/quote/${symbol}`);
    return response.data;
  },

  // Order methods
  async submitOrder(order: OrderData): Promise<OrderResult> {
    const response = await api.post('/trading/order', order);
    return response.data;
  },

  async placeOrder(order: OrderData): Promise<OrderResult> {
    const response = await api.post('/trading/order', order);
    return response.data;
  },

  // Recurring investment methods
  async createRecurringInvestment(
    investment: RecurringInvestmentCreate
  ): Promise<RecurringInvestment> {
    const response = await api.post('/trading/recurring', investment);
    return response.data;
  },

  async getRecurringInvestments(): Promise<RecurringInvestment[]> {
    const response = await api.get('/trading/recurring');
    return response.data;
  },

  async cancelRecurringInvestment(id: number): Promise<{ message: string }> {
    const response = await api.delete(`/trading/recurring/${id}`);
    return response.data;
  },

  async pauseRecurringInvestment(id: number): Promise<RecurringInvestment> {
    const response = await api.patch(`/trading/recurring/${id}/pause`);
    return response.data;
  },

  async resumeRecurringInvestment(id: number): Promise<RecurringInvestment> {
    const response = await api.patch(`/trading/recurring/${id}/resume`);
    return response.data;
  },
};

export default tradingService;
