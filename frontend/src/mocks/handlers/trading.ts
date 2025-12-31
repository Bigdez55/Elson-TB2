import { http, HttpResponse, delay } from 'msw';

// Default test data
export const defaultTrade: {
  id: number;
  symbol: string;
  trade_type: string;
  order_type: string;
  quantity: number;
  price: number | null;
  status: string;
  created_at: string;
  updated_at: string;
  executed_at: string | null;
  executed_price: number | null;
} = {
  id: 1,
  symbol: 'AAPL',
  trade_type: 'buy',
  order_type: 'market',
  quantity: 10,
  price: null,
  status: 'pending',
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
  executed_at: null,
  executed_price: null,
};

export const defaultPosition = {
  id: 1,
  symbol: 'AAPL',
  asset_type: 'stock',
  quantity: 10,
  average_cost: 150.00,
  current_price: 152.50,
  market_value: 1525.00,
  unrealized_gain_loss: 25.00,
  unrealized_gain_loss_percentage: 1.67,
};

export const defaultTradingStats = {
  total_trades: 50,
  winning_trades: 30,
  losing_trades: 20,
  win_rate: 0.6,
  total_pnl: 2500.00,
  average_win: 150.00,
  average_loss: -75.00,
  best_trade: 500.00,
  worst_trade: -200.00,
  sharpe_ratio: 1.25,
};

// Mutable state for tests that need to track orders
let orders: typeof defaultTrade[] = [];
let tradeHistory: typeof defaultTrade[] = [];

export const resetTradingState = () => {
  orders = [];
  tradeHistory = [];
};

export const tradingHandlers = [
  // Place order
  http.post('/api/v1/trading/order', async ({ request }) => {
    await delay(50);

    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    }

    const body = await request.json() as {
      symbol: string;
      trade_type: string;
      order_type: string;
      quantity: number;
      price?: number;
    };

    // Simulate insufficient funds
    if (body.quantity > 100000) {
      return HttpResponse.json(
        { detail: 'Insufficient funds' },
        { status: 400 }
      );
    }

    // Simulate invalid symbol
    if (body.symbol === 'INVALID') {
      return HttpResponse.json(
        { detail: 'Invalid symbol' },
        { status: 400 }
      );
    }

    const newOrder = {
      id: orders.length + 1,
      symbol: body.symbol,
      trade_type: body.trade_type,
      order_type: body.order_type,
      quantity: body.quantity,
      price: body.price || null,
      status: 'pending',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      executed_at: null,
      executed_price: null,
    };

    orders.push(newOrder);

    return HttpResponse.json(newOrder, { status: 201 });
  }),

  // Cancel order
  http.post('/api/v1/trading/cancel', async ({ request }) => {
    await delay(50);

    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    }

    const body = await request.json() as { trade_id: number };

    const orderIndex = orders.findIndex((o) => o.id === body.trade_id);
    if (orderIndex === -1) {
      return HttpResponse.json(
        { detail: 'Order not found' },
        { status: 404 }
      );
    }

    const cancelledOrder = {
      ...orders[orderIndex],
      status: 'cancelled',
      updated_at: new Date().toISOString(),
    };

    orders[orderIndex] = cancelledOrder;

    return HttpResponse.json(cancelledOrder);
  }),

  // Get open orders
  http.get('/api/v1/trading/orders', async ({ request }) => {
    await delay(50);

    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    }

    // Return only pending orders
    const openOrders = orders.filter((o) => o.status === 'pending');

    return HttpResponse.json(openOrders);
  }),

  // Get trade history
  http.get('/api/v1/trading/history', async ({ request }) => {
    await delay(50);

    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    }

    const url = new URL(request.url);
    const limit = parseInt(url.searchParams.get('limit') || '100', 10);

    // Return completed trades from history
    const history = tradeHistory.length > 0
      ? tradeHistory.slice(0, limit)
      : [
          {
            ...defaultTrade,
            id: 1,
            status: 'executed',
            executed_at: '2023-01-01T00:01:00Z',
            executed_price: 150.00,
          },
        ];

    return HttpResponse.json(history);
  }),

  // Get positions
  http.get('/api/v1/trading/positions', async ({ request }) => {
    await delay(50);

    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    }

    return HttpResponse.json([defaultPosition]);
  }),

  // Get trading stats
  http.get('/api/v1/trading/stats', async ({ request }) => {
    await delay(50);

    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    }

    return HttpResponse.json(defaultTradingStats);
  }),

  // Validate symbol
  http.get('/api/v1/trading/validate/:symbol', async ({ params, request }) => {
    await delay(50);

    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    }

    const { symbol } = params;

    if (symbol === 'INVALID') {
      return HttpResponse.json(
        { valid: false, message: 'Symbol not found' },
        { status: 404 }
      );
    }

    return HttpResponse.json({
      valid: true,
      symbol,
      name: `${symbol} Inc.`,
      exchange: 'NASDAQ',
    });
  }),

  // Get account info (for RTK Query tradingApi)
  http.get('/api/v1/trading/account', async ({ request }) => {
    await delay(50);

    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    }

    return HttpResponse.json({
      id: 1,
      account_number: 'TEST-123456',
      buying_power: 50000.00,
      cash: 25000.00,
      portfolio_value: 75000.00,
      equity: 75000.00,
      last_equity: 74500.00,
      day_trade_count: 0,
      pattern_day_trader: false,
      status: 'active',
    });
  }),

  // Batch data endpoint
  http.get('/api/v1/trading/batch-data', async ({ request }) => {
    await delay(50);

    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    }

    return HttpResponse.json({
      account: {
        buying_power: 50000.00,
        cash: 25000.00,
        portfolio_value: 75000.00,
      },
      positions: [defaultPosition],
      orders: orders.filter((o) => o.status === 'pending'),
      history: tradeHistory.slice(0, 10),
    });
  }),

  // Cancel order by ID
  http.post('/api/v1/trading/orders/:orderId/cancel', async ({ params, request }) => {
    await delay(50);

    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    }

    const orderId = parseInt(params.orderId as string, 10);
    const orderIndex = orders.findIndex((o) => o.id === orderId);

    if (orderIndex === -1) {
      return HttpResponse.json({ detail: 'Order not found' }, { status: 404 });
    }

    orders[orderIndex] = {
      ...orders[orderIndex],
      status: 'cancelled',
      updated_at: new Date().toISOString(),
    };

    return HttpResponse.json(orders[orderIndex]);
  }),
];
