import { http, HttpResponse, delay } from 'msw';

// Default risk data
export const defaultRiskMetrics = {
  portfolio_value: 100000.00,
  daily_var: 2500.00,
  portfolio_beta: 1.15,
  sharpe_ratio: 1.45,
  max_drawdown: -8.50,
  volatility: 15.20,
  concentration_risk: 0.35,
  sector_concentration: {
    Technology: 0.88,
    Healthcare: 0.05,
    Finance: 0.07,
  },
  largest_position_pct: 41.40,
  cash_percentage: 25.00,
  leverage_ratio: 0.00,
};

export const defaultRiskLimits = {
  max_position_size: 0.10, // 10%
  max_sector_concentration: 0.40, // 40%
  max_daily_loss: 0.05, // 5%
  max_leverage: 2.0,
  min_cash_percentage: 0.05, // 5%
  max_correlation: 0.80,
  stop_loss_enabled: true,
  stop_loss_percentage: 0.08, // 8%
  take_profit_enabled: true,
  take_profit_percentage: 0.15, // 15%
};

export const defaultCircuitBreakers = [
  {
    id: 1,
    name: 'Daily Loss Limit',
    trigger_condition: 'daily_loss > 5%',
    status: 'inactive',
    last_triggered: null,
    action: 'halt_trading',
  },
  {
    id: 2,
    name: 'Volatility Spike',
    trigger_condition: 'vix > 35',
    status: 'inactive',
    last_triggered: null,
    action: 'reduce_position_sizes',
  },
  {
    id: 3,
    name: 'Rapid Drawdown',
    trigger_condition: 'drawdown_30min > 3%',
    status: 'inactive',
    last_triggered: null,
    action: 'halt_trading',
  },
];

export const riskHandlers = [
  // Assess trade risk
  http.post('/api/v1/risk/assess-trade', async ({ request }) => {
    await delay(50);

    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    }

    const body = await request.json() as {
      symbol: string;
      trade_type: 'buy' | 'sell';
      quantity: number;
      price?: number;
    };

    // Calculate risk score based on trade size
    const tradeValue = body.quantity * (body.price || 150);
    const portfolioImpact = tradeValue / 100000; // Assume $100k portfolio
    let riskScore = Math.min(100, portfolioImpact * 100);
    let checkResult = 'approved';
    const violations: string[] = [];
    const warnings: string[] = [];

    // Check position size limit
    if (portfolioImpact > 0.10) {
      violations.push('Position size exceeds 10% limit');
      checkResult = 'rejected';
      riskScore = 90;
    } else if (portfolioImpact > 0.05) {
      warnings.push('Position size is above 5% recommended limit');
      checkResult = 'warning';
      riskScore = 70;
    }

    // Check for concentrated sectors
    if (body.symbol === 'AAPL' || body.symbol === 'MSFT' || body.symbol === 'GOOGL') {
      if (portfolioImpact > 0.03) {
        warnings.push('Adding to already concentrated Technology sector');
      }
    }

    return HttpResponse.json({
      trade_id: `temp-${Date.now()}`,
      symbol: body.symbol,
      risk_level: riskScore > 70 ? 'high' : riskScore > 40 ? 'medium' : 'low',
      risk_score: riskScore,
      check_result: checkResult,
      violations,
      warnings,
      impact_analysis: {
        portfolio_impact: portfolioImpact,
        new_position_weight: portfolioImpact * 100,
        sector_exposure_change: portfolioImpact * 0.5,
      },
      recommended_action: checkResult === 'rejected' ? 'Reduce position size' : null,
      max_allowed_quantity: Math.floor((100000 * 0.10) / (body.price || 150)),
    });
  }),

  // Get portfolio risk metrics
  http.get('/api/v1/risk/portfolio-metrics', async ({ request }) => {
    await delay(50);

    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    }

    return HttpResponse.json(defaultRiskMetrics);
  }),

  // Get position risk analysis
  http.get('/api/v1/risk/position-analysis', async ({ request }) => {
    await delay(50);

    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    }

    return HttpResponse.json([
      {
        symbol: 'AAPL',
        position_size: 7625.00,
        weight: 10.17,
        risk_score: 25,
        beta: 1.20,
        volatility: 18.50,
        var_contribution: 250.00,
        max_loss_potential: 625.00,
      },
      {
        symbol: 'GOOGL',
        position_size: 28000.00,
        weight: 37.33,
        risk_score: 65,
        beta: 1.10,
        volatility: 22.00,
        var_contribution: 1100.00,
        max_loss_potential: 2800.00,
      },
      {
        symbol: 'MSFT',
        position_size: 31050.00,
        weight: 41.40,
        risk_score: 55,
        beta: 0.95,
        volatility: 16.50,
        var_contribution: 850.00,
        max_loss_potential: 2050.00,
      },
    ]);
  }),

  // Get circuit breakers
  http.get('/api/v1/risk/circuit-breakers', async ({ request }) => {
    await delay(50);

    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    }

    return HttpResponse.json(defaultCircuitBreakers);
  }),

  // Get risk limits
  http.get('/api/v1/risk/risk-limits', async ({ request }) => {
    await delay(50);

    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    }

    return HttpResponse.json(defaultRiskLimits);
  }),

  // Get symbol risk score
  http.get('/api/v1/risk/risk-score/:symbol', async ({ params, request }) => {
    await delay(50);

    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    }

    const { symbol } = params;

    // Return risk score based on symbol
    const riskScores: Record<string, number> = {
      AAPL: 25,
      GOOGL: 35,
      MSFT: 20,
      TSLA: 75,
      GME: 95,
    };

    const score = riskScores[symbol as string] || 50;

    return HttpResponse.json({
      symbol,
      risk_score: score,
      risk_level: score > 70 ? 'high' : score > 40 ? 'medium' : 'low',
      factors: {
        volatility: score * 0.4,
        beta: score * 0.3,
        liquidity: score * 0.2,
        sector_risk: score * 0.1,
      },
      recommendation: score > 70 ? 'Consider reducing exposure' : 'Acceptable risk level',
    });
  }),

  // Validate portfolio
  http.post('/api/v1/risk/validate-portfolio', async ({ request }) => {
    await delay(50);

    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 });
    }

    return HttpResponse.json({
      is_valid: true,
      violations: [],
      warnings: [
        'Technology sector concentration is at 88%, above recommended 40%',
      ],
      recommendations: [
        'Consider diversifying into other sectors',
        'Reduce GOOGL or MSFT position to improve sector balance',
      ],
      risk_score: 45,
      last_validated: new Date().toISOString(),
    });
  }),
];
