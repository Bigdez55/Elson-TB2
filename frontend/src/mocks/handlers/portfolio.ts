import { http, HttpResponse, delay } from 'msw';

// Default portfolio data
export const defaultPortfolio = {
  id: 1,
  name: 'Main Portfolio',
  description: 'Primary trading portfolio',
  total_value: 100000.00,
  cash_balance: 25000.00,
  invested_amount: 75000.00,
  total_return: 5000.00,
  total_return_percentage: 5.26,
  auto_rebalance: false,
  is_active: true,
  created_at: '2023-01-01T00:00:00Z',
  updated_at: new Date().toISOString(),
};

export const defaultHoldings = [
  {
    id: 1,
    symbol: 'AAPL',
    asset_type: 'stock',
    quantity: 50,
    average_cost: 140.00,
    current_price: 152.50,
    market_value: 7625.00,
    unrealized_gain_loss: 625.00,
    unrealized_gain_loss_percentage: 8.93,
    weight: 10.17,
  },
  {
    id: 2,
    symbol: 'GOOGL',
    asset_type: 'stock',
    quantity: 10,
    average_cost: 2700.00,
    current_price: 2800.00,
    market_value: 28000.00,
    unrealized_gain_loss: 1000.00,
    unrealized_gain_loss_percentage: 3.70,
    weight: 37.33,
  },
  {
    id: 3,
    symbol: 'MSFT',
    asset_type: 'stock',
    quantity: 100,
    average_cost: 290.00,
    current_price: 310.50,
    market_value: 31050.00,
    unrealized_gain_loss: 2050.00,
    unrealized_gain_loss_percentage: 7.07,
    weight: 41.40,
  },
];

export const defaultPerformance = {
  daily_return: 0.75,
  weekly_return: 2.50,
  monthly_return: 5.26,
  yearly_return: 18.50,
  total_return: 5000.00,
  total_return_percentage: 5.26,
  benchmark_return: 4.20,
  alpha: 1.06,
  beta: 1.15,
  sharpe_ratio: 1.45,
  max_drawdown: -8.50,
  volatility: 15.20,
};

export const portfolioHandlers = [
  // Get portfolio summary
  http.get('/api/v1/portfolio/', async ({ request }) => {
    await delay(50);

    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    }

    return HttpResponse.json({
      portfolio: defaultPortfolio,
      holdings: defaultHoldings,
      total_positions: defaultHoldings.length,
    });
  }),

  // Get portfolio details
  http.get('/api/v1/portfolio/details', async ({ request }) => {
    await delay(50);

    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    }

    return HttpResponse.json({
      ...defaultPortfolio,
      holdings: defaultHoldings,
      performance: defaultPerformance,
    });
  }),

  // Get holdings
  http.get('/api/v1/portfolio/holdings', async ({ request }) => {
    await delay(50);

    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    }

    return HttpResponse.json(defaultHoldings);
  }),

  // Update portfolio
  http.put('/api/v1/portfolio/', async ({ request }) => {
    await delay(50);

    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    }

    const body = await request.json() as {
      name?: string;
      description?: string;
      cash_balance?: number;
      auto_rebalance?: boolean;
    };

    const updatedPortfolio = {
      ...defaultPortfolio,
      ...body,
      updated_at: new Date().toISOString(),
    };

    return HttpResponse.json(updatedPortfolio);
  }),

  // Get performance
  http.get('/api/v1/portfolio/performance', async ({ request }) => {
    await delay(50);

    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    }

    return HttpResponse.json(defaultPerformance);
  }),

  // Refresh portfolio data
  http.post('/api/v1/portfolio/refresh', async ({ request }) => {
    await delay(100); // Slightly longer for refresh

    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    }

    return HttpResponse.json({
      message: 'Portfolio data refreshed',
      last_updated: new Date().toISOString(),
    });
  }),
];
