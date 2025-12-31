import { http, HttpResponse, delay } from 'msw';

// Default test data
export const createQuote = (symbol: string, overrides?: Partial<Quote>) => ({
  symbol,
  open: 150.00,
  high: 155.00,
  low: 149.00,
  price: 152.50,
  volume: 10000000,
  change: 2.50,
  change_percent: 1.67,
  previous_close: 150.00,
  source: 'mock',
  timestamp: new Date().toISOString(),
  ...overrides,
});

interface Quote {
  symbol: string;
  open: number;
  high: number;
  low: number;
  price: number;
  volume: number;
  change: number;
  change_percent: number;
  previous_close: number;
  source: string;
  timestamp: string;
}

export const defaultAssets = [
  {
    id: 1,
    symbol: 'AAPL',
    name: 'Apple Inc.',
    asset_type: 'stock',
    exchange: 'NASDAQ',
    sector: 'Technology',
    industry: 'Consumer Electronics',
    is_tradable: true,
  },
  {
    id: 2,
    symbol: 'GOOGL',
    name: 'Alphabet Inc.',
    asset_type: 'stock',
    exchange: 'NASDAQ',
    sector: 'Technology',
    industry: 'Internet Services',
    is_tradable: true,
  },
  {
    id: 3,
    symbol: 'MSFT',
    name: 'Microsoft Corporation',
    asset_type: 'stock',
    exchange: 'NASDAQ',
    sector: 'Technology',
    industry: 'Software',
    is_tradable: true,
  },
];

// Stored quotes for consistency
const quoteCache: Record<string, Quote> = {
  AAPL: createQuote('AAPL', { price: 152.50 }),
  GOOGL: createQuote('GOOGL', { price: 2800.00, change: 25.00, change_percent: 0.90 }),
  MSFT: createQuote('MSFT', { price: 310.50, change: 5.50, change_percent: 1.80 }),
};

export const marketHandlers = [
  // Get single quote
  http.get('/api/v1/market/quote/:symbol', async ({ params }) => {
    await delay(50);

    const { symbol } = params;
    const upperSymbol = (symbol as string).toUpperCase();

    // Simulate invalid symbol
    if (upperSymbol === 'INVALID') {
      return HttpResponse.json(
        { detail: 'Symbol not found' },
        { status: 404 }
      );
    }

    // Return cached quote or create new one
    const quote = quoteCache[upperSymbol] || createQuote(upperSymbol);

    return HttpResponse.json(quote);
  }),

  // Get multiple quotes
  http.post('/api/v1/market/quotes', async ({ request }) => {
    await delay(50);

    const symbols = await request.json() as string[];

    const quotes = symbols.map((symbol) => {
      const upperSymbol = symbol.toUpperCase();
      return quoteCache[upperSymbol] || createQuote(upperSymbol);
    });

    return HttpResponse.json({
      quotes,
      timestamp: new Date().toISOString(),
    });
  }),

  // Get assets
  http.get('/api/v1/market/assets', async ({ request }) => {
    await delay(50);

    const url = new URL(request.url);
    const assetType = url.searchParams.get('asset_type');
    const sector = url.searchParams.get('sector');
    const limit = parseInt(url.searchParams.get('limit') || '100', 10);

    let filteredAssets = [...defaultAssets];

    if (assetType) {
      filteredAssets = filteredAssets.filter((a) => a.asset_type === assetType);
    }

    if (sector) {
      filteredAssets = filteredAssets.filter((a) => a.sector === sector);
    }

    return HttpResponse.json(filteredAssets.slice(0, limit));
  }),

  // Get historical data
  http.get('/api/v1/market/history/:symbol', async ({ params, request }) => {
    await delay(50);

    const { symbol } = params;
    const url = new URL(request.url);
    const timeframe = url.searchParams.get('timeframe') || '1day';
    const limit = parseInt(url.searchParams.get('limit') || '100', 10);

    if (symbol === 'INVALID') {
      return HttpResponse.json(
        { detail: 'Symbol not found' },
        { status: 404 }
      );
    }

    // Generate mock historical data
    const data = [];
    const now = new Date();
    let price = 150.00;

    for (let i = 0; i < limit; i++) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);

      // Random price movement
      const change = (Math.random() - 0.5) * 5;
      price += change;

      data.push({
        date: date.toISOString().split('T')[0],
        open: price - Math.random() * 2,
        high: price + Math.random() * 3,
        low: price - Math.random() * 3,
        close: price,
        volume: Math.floor(Math.random() * 10000000) + 1000000,
      });
    }

    return HttpResponse.json({
      symbol,
      timeframe,
      data: data.reverse(),
    });
  }),

  // Create asset
  http.post('/api/v1/market/assets', async ({ request }) => {
    await delay(50);

    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    }

    const body = await request.json() as {
      symbol: string;
      name: string;
      asset_type: string;
      exchange?: string;
      sector?: string;
      industry?: string;
    };

    const newAsset = {
      id: defaultAssets.length + 1,
      symbol: body.symbol.toUpperCase(),
      name: body.name,
      asset_type: body.asset_type,
      exchange: body.exchange || 'NYSE',
      sector: body.sector || 'Unknown',
      industry: body.industry || 'Unknown',
      is_tradable: true,
    };

    return HttpResponse.json(newAsset, { status: 201 });
  }),

  // Enhanced market data endpoints (for marketDataApi RTK Query)
  http.get('/api/v1/market-enhanced/quote/:symbol', async ({ params }) => {
    await delay(50);

    const { symbol } = params;
    const upperSymbol = (symbol as string).toUpperCase();

    if (upperSymbol === 'INVALID') {
      return HttpResponse.json({ detail: 'Symbol not found' }, { status: 404 });
    }

    const quote = quoteCache[upperSymbol] || createQuote(upperSymbol);

    return HttpResponse.json({
      ...quote,
      statistics: {
        min_price: quote.low,
        max_price: quote.high,
        avg_price: (quote.high + quote.low) / 2,
      },
    });
  }),

  http.get('/api/v1/market-enhanced/quotes', async ({ request }) => {
    await delay(50);

    const url = new URL(request.url);
    const symbolsParam = url.searchParams.get('symbols') || '';
    const symbols = symbolsParam.split(',').filter(Boolean);

    const quotes = symbols.map((symbol) => {
      const upperSymbol = symbol.toUpperCase();
      return quoteCache[upperSymbol] || createQuote(upperSymbol);
    });

    return HttpResponse.json({
      quotes,
      timestamp: new Date().toISOString(),
    });
  }),

  http.get('/api/v1/market-enhanced/search', async ({ request }) => {
    await delay(50);

    const url = new URL(request.url);
    const query = (url.searchParams.get('query') || '').toLowerCase();

    const results = defaultAssets.filter(
      (a) =>
        a.symbol.toLowerCase().includes(query) ||
        a.name.toLowerCase().includes(query)
    );

    return HttpResponse.json({
      results,
      total: results.length,
    });
  }),

  http.get('/api/v1/market-enhanced/historical/:symbol', async ({ params, request }) => {
    await delay(50);

    const { symbol } = params;
    const url = new URL(request.url);
    const period = url.searchParams.get('period') || '1M';

    if (symbol === 'INVALID') {
      return HttpResponse.json({ detail: 'Symbol not found' }, { status: 404 });
    }

    // Generate historical data based on period
    const periodDays: Record<string, number> = {
      '1D': 1,
      '1W': 7,
      '1M': 30,
      '3M': 90,
      '1Y': 365,
    };

    const days = periodDays[period] || 30;
    const data = [];
    let price = 150.00;

    for (let i = 0; i < days; i++) {
      const date = new Date();
      date.setDate(date.getDate() - (days - i));
      const change = (Math.random() - 0.5) * 5;
      price += change;

      data.push({
        date: date.toISOString(),
        close: price,
        volume: Math.floor(Math.random() * 10000000) + 1000000,
      });
    }

    return HttpResponse.json({
      symbol,
      period,
      data,
    });
  }),

  http.get('/api/v1/market-enhanced/health', async () => {
    await delay(50);

    return HttpResponse.json({
      status: 'healthy',
      providers: {
        yahoo_finance: { status: 'online', latency_ms: 45 },
        alpha_vantage: { status: 'online', latency_ms: 120 },
      },
      last_check: new Date().toISOString(),
    });
  }),
];
