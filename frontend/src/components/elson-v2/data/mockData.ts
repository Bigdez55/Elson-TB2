import type { Holding, Stock, Crypto, FamilyMember, Goal, SubscriptionPlan, User } from '../types';

export const user: User = {
  name: 'Alex Thompson',
  email: 'alex@example.com',
  tier: 'Premium',
  risk: 'Moderate',
};

export const holdings: Holding[] = [
  {
    symbol: 'AAPL',
    name: 'Apple Inc.',
    shares: 50,
    avgCost: 145,
    currentPrice: 178.5,
    value: 8925,
    gain: 1675,
    gainPercent: 23.1,
  },
  {
    symbol: 'GOOGL',
    name: 'Alphabet Inc.',
    shares: 20,
    avgCost: 125,
    currentPrice: 141.8,
    value: 2836,
    gain: 336,
    gainPercent: 13.44,
  },
  {
    symbol: 'MSFT',
    name: 'Microsoft Corp.',
    shares: 35,
    avgCost: 310,
    currentPrice: 378.9,
    value: 13261.5,
    gain: 2411.5,
    gainPercent: 22.23,
  },
  {
    symbol: 'NVDA',
    name: 'NVIDIA Corp.',
    shares: 15,
    avgCost: 450,
    currentPrice: 721.33,
    value: 10819.95,
    gain: 4069.95,
    gainPercent: 60.3,
  },
  {
    symbol: 'TSLA',
    name: 'Tesla Inc.',
    shares: 25,
    avgCost: 220,
    currentPrice: 248.5,
    value: 6212.5,
    gain: 712.5,
    gainPercent: 12.95,
  },
];

export const stocks: Stock[] = [
  { symbol: 'AAPL', name: 'Apple Inc.', price: 178.5, change: 2.35, pct: 1.33 },
  { symbol: 'GOOGL', name: 'Alphabet Inc.', price: 141.8, change: -1.2, pct: -0.84 },
  { symbol: 'MSFT', name: 'Microsoft Corp.', price: 378.9, change: 5.6, pct: 1.5 },
  { symbol: 'NVDA', name: 'NVIDIA Corp.', price: 721.33, change: 15.4, pct: 2.18 },
  { symbol: 'TSLA', name: 'Tesla Inc.', price: 248.5, change: -3.8, pct: -1.51 },
  { symbol: 'AMZN', name: 'Amazon.com', price: 178.25, change: 1.85, pct: 1.05 },
  { symbol: 'META', name: 'Meta Platforms', price: 505.75, change: 8.2, pct: 1.65 },
  { symbol: 'AMD', name: 'AMD Inc.', price: 164.3, change: -2.1, pct: -1.26 },
];

export const crypto: Crypto[] = [
  { symbol: 'BTC', name: 'Bitcoin', price: 67450, change: 2.35, hold: 0.25 },
  { symbol: 'ETH', name: 'Ethereum', price: 3520, change: -1.2, hold: 2.5 },
  { symbol: 'SOL', name: 'Solana', price: 148.5, change: 5.8, hold: 15 },
];

export const family: FamilyMember[] = [
  {
    id: '1',
    name: 'Alex Thompson',
    role: 'Owner',
    accountType: 'Primary',
    status: 'Active',
    balance: 42054.95,
  },
  {
    id: '2',
    name: 'Sarah Thompson',
    role: 'Adult',
    accountType: 'Individual',
    status: 'Active',
    balance: 15230,
  },
  {
    id: '3',
    name: 'Jake Thompson',
    role: 'Teen',
    accountType: 'Custodial',
    status: 'Active',
    balance: 2500,
  },
  {
    id: '4',
    name: 'Emma Thompson',
    role: 'Child',
    accountType: 'UGMA',
    status: 'Restricted',
    balance: 1200,
  },
];

export const goals: Goal[] = [
  { id: '1', name: 'Emergency Fund', target: 15000, current: 12500, icon: '🛡️' },
  { id: '2', name: 'Vacation', target: 5000, current: 3200, icon: '✈️' },
  { id: '3', name: 'Down Payment', target: 50000, current: 18500, icon: '🏠' },
];

export const plans: SubscriptionPlan[] = [
  {
    id: 'free',
    name: 'Free',
    price: 0,
    apy: '3.5%',
    trades: '3/day',
    features: ['Basic trading', 'Market data', 'Mobile app'],
  },
  {
    id: 'growth',
    name: 'Growth',
    price: 9.99,
    apy: '4.0%',
    trades: 'Unlimited',
    features: ['Everything in Free', 'AI insights', 'Price alerts', 'Extended hours'],
  },
  {
    id: 'premium',
    name: 'Premium',
    price: 24.99,
    apy: '4.5%',
    trades: 'Unlimited',
    features: [
      'Everything in Growth',
      'AI Trading Bot',
      'Advanced analytics',
      'Priority support',
    ],
    popular: true,
  },
  {
    id: 'elite',
    name: 'Elite',
    price: 49.99,
    apy: '5.0%',
    trades: 'Unlimited',
    features: [
      'Everything in Premium',
      'Family accounts',
      'Tax optimization',
      'Dedicated advisor',
      'Exclusive features',
    ],
  },
];
