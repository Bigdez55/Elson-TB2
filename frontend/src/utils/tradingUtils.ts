/**
 * Trading utility functions
 * Fee calculations, order estimates, and trading helpers
 */

// Fee constants - matching backend configuration
export const TRADING_FEES = {
  COMMISSION_RATE: 0.0035, // 0.35%
  MIN_COMMISSION: 0.50, // $0.50 minimum
  PAPER_TRADING_FEE_PER_SHARE: 0.005, // $0.005 per share for paper trading
} as const;

/**
 * Fee breakdown result
 */
export interface FeeBreakdown {
  commission: number;
  fees: number;
  totalFees: number;
  feeDescription: string;
}

/**
 * Order estimate result
 */
export interface OrderEstimate {
  shares: number;
  cost: number;
  fees: FeeBreakdown;
  totalAmount: number; // Total including fees (add for buy, subtract for sell)
  averagePricePerShare: number;
}

/**
 * Calculate trading fees based on order value and trading mode
 *
 * @param orderValue - Total order value in dollars
 * @param shares - Number of shares in the order
 * @param isPaperTrading - Whether this is a paper trading order
 * @returns Fee breakdown object
 */
export function calculateFees(
  orderValue: number,
  shares: number,
  isPaperTrading: boolean = true
): FeeBreakdown {
  if (isPaperTrading) {
    // Paper trading: $0.005 per share
    const fees = shares * TRADING_FEES.PAPER_TRADING_FEE_PER_SHARE;
    return {
      commission: 0,
      fees: Math.round(fees * 100) / 100, // Round to cents
      totalFees: Math.round(fees * 100) / 100,
      feeDescription: `$${TRADING_FEES.PAPER_TRADING_FEE_PER_SHARE}/share paper trading fee`,
    };
  }

  // Live trading: 0.35% commission with $0.50 minimum
  const rawCommission = orderValue * TRADING_FEES.COMMISSION_RATE;
  const commission = Math.max(rawCommission, TRADING_FEES.MIN_COMMISSION);

  return {
    commission: Math.round(commission * 100) / 100,
    fees: 0,
    totalFees: Math.round(commission * 100) / 100,
    feeDescription: `${TRADING_FEES.COMMISSION_RATE * 100}% commission (min $${TRADING_FEES.MIN_COMMISSION})`,
  };
}

/**
 * Calculate order estimate for dollar-based investing
 *
 * @param dollarAmount - Amount in dollars to invest
 * @param pricePerShare - Current price per share
 * @param orderType - 'buy' or 'sell'
 * @param isPaperTrading - Whether this is paper trading
 * @returns Order estimate including shares and fees
 */
export function calculateDollarBasedOrder(
  dollarAmount: number,
  pricePerShare: number,
  orderType: 'buy' | 'sell' = 'buy',
  isPaperTrading: boolean = true
): OrderEstimate {
  if (dollarAmount <= 0 || pricePerShare <= 0) {
    return {
      shares: 0,
      cost: 0,
      fees: { commission: 0, fees: 0, totalFees: 0, feeDescription: '' },
      totalAmount: 0,
      averagePricePerShare: pricePerShare,
    };
  }

  // For dollar-based, we need to calculate shares from the amount
  const estimatedShares = dollarAmount / pricePerShare;
  const fees = calculateFees(dollarAmount, estimatedShares, isPaperTrading);

  const totalAmount = orderType === 'buy'
    ? dollarAmount + fees.totalFees
    : dollarAmount - fees.totalFees;

  return {
    shares: estimatedShares,
    cost: dollarAmount,
    fees,
    totalAmount: Math.round(totalAmount * 100) / 100,
    averagePricePerShare: pricePerShare,
  };
}

/**
 * Calculate order estimate for share-based investing
 *
 * @param shareQuantity - Number of shares
 * @param pricePerShare - Current price per share
 * @param orderType - 'buy' or 'sell'
 * @param isPaperTrading - Whether this is paper trading
 * @returns Order estimate including cost and fees
 */
export function calculateShareBasedOrder(
  shareQuantity: number,
  pricePerShare: number,
  orderType: 'buy' | 'sell' = 'buy',
  isPaperTrading: boolean = true
): OrderEstimate {
  if (shareQuantity <= 0 || pricePerShare <= 0) {
    return {
      shares: 0,
      cost: 0,
      fees: { commission: 0, fees: 0, totalFees: 0, feeDescription: '' },
      totalAmount: 0,
      averagePricePerShare: pricePerShare,
    };
  }

  const cost = shareQuantity * pricePerShare;
  const fees = calculateFees(cost, shareQuantity, isPaperTrading);

  const totalAmount = orderType === 'buy'
    ? cost + fees.totalFees
    : cost - fees.totalFees;

  return {
    shares: shareQuantity,
    cost: Math.round(cost * 100) / 100,
    fees,
    totalAmount: Math.round(totalAmount * 100) / 100,
    averagePricePerShare: pricePerShare,
  };
}

/**
 * Format shares with appropriate precision
 * Whole shares: 2 decimal places
 * Fractional shares: up to 6 decimal places
 */
export function formatShares(shares: number): string {
  if (shares === 0) return '0';

  if (shares >= 1 && Number.isInteger(shares)) {
    return shares.toLocaleString();
  }

  // For fractional shares, show up to 6 decimal places but trim trailing zeros
  const formatted = shares.toFixed(6);
  return parseFloat(formatted).toString();
}

/**
 * Quick invest preset amounts (Acorns/Stash style)
 */
export const QUICK_INVEST_AMOUNTS = [1, 5, 10, 25, 50, 100] as const;

/**
 * Default investment amounts by user type
 */
export const DEFAULT_INVESTMENTS = {
  BEGINNER: [1, 5, 10],
  STANDARD: [5, 10, 25, 50],
  PREMIUM: [10, 25, 50, 100, 250],
} as const;

/**
 * Check if an order meets minimum investment requirements
 */
export function meetsMinimumInvestment(amount: number, minAmount: number = 0.01): boolean {
  return amount >= minAmount;
}

/**
 * Calculate the maximum shares purchasable with available funds
 */
export function maxSharesForBudget(
  availableFunds: number,
  pricePerShare: number,
  isPaperTrading: boolean = true
): number {
  if (availableFunds <= 0 || pricePerShare <= 0) return 0;

  // Account for fees when calculating max shares
  // This is an approximation - actual fees depend on final share count
  const feeRate = isPaperTrading
    ? TRADING_FEES.PAPER_TRADING_FEE_PER_SHARE / pricePerShare
    : TRADING_FEES.COMMISSION_RATE;

  const effectiveFunds = availableFunds / (1 + feeRate);
  return effectiveFunds / pricePerShare;
}

/**
 * Validate order parameters
 */
export interface OrderValidation {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

export function validateOrder(
  orderType: 'buy' | 'sell',
  amount: number,
  availableFunds?: number,
  availableShares?: number,
  shares?: number
): OrderValidation {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (amount <= 0) {
    errors.push('Order amount must be greater than zero');
  }

  if (amount < 0.01) {
    errors.push('Minimum order amount is $0.01');
  }

  if (orderType === 'buy' && availableFunds !== undefined) {
    if (amount > availableFunds) {
      errors.push(`Insufficient funds. Available: $${availableFunds.toFixed(2)}`);
    } else if (amount > availableFunds * 0.9) {
      warnings.push('This order will use most of your available funds');
    }
  }

  if (orderType === 'sell' && availableShares !== undefined && shares !== undefined) {
    if (shares > availableShares) {
      errors.push(`Insufficient shares. Available: ${formatShares(availableShares)}`);
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
  };
}
