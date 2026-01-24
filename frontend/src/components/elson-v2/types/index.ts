export interface Holding {
  symbol: string;
  name: string;
  shares: number;
  avgCost: number;
  currentPrice: number;
  value: number;
  gain: number;
  gainPercent: number;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

export interface FamilyMember {
  id: string;
  name: string;
  role: string;
  accountType: string;
  status: string;
  balance: number;
}

export interface Goal {
  id: string;
  name: string;
  target: number;
  current: number;
  icon: string;
}

export interface Stock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  pct: number;
}

export interface Crypto {
  symbol: string;
  name: string;
  price: number;
  change: number;
  hold: number;
}

export interface SubscriptionPlan {
  id: string;
  name: string;
  price: number;
  apy: string;
  trades: string;
  features: string[];
  popular?: boolean;
}

export interface User {
  name: string;
  email: string;
  tier: string;
  risk: string;
}

export type TabId = 'dashboard' | 'ai' | 'invest' | 'wealth' | 'account';
export type TradingMode = 'paper' | 'live';
