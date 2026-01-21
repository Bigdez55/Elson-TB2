// Elson Trading Platform Type Definitions

// User tier levels for subscription-based features
export type UserTier = 'Starter' | 'Growth' | 'Wealth';

// Trading mode (Paper for simulation, Live for real trading)
export type TradingMode = 'Paper' | 'Live';

// Main navigation pages
export type ActivePage = 'Dashboard' | 'Elson AI' | 'Invest' | 'Learn' | 'Account';

// Family member roles for family accounts feature
export type FamilyRole = 'owner' | 'adult' | 'teen' | 'child';

// Family member data structure
export interface FamilyMember {
  id: string;
  name: string;
  role: FamilyRole;
  value: number;
  change: number;
  pendingApprovals?: number;
}

// Stock/Asset holding data structure
export interface Holding {
  symbol: string;
  name: string;
  shares: string;
  value: string;
  change: number;
  color: string;
}

// AI insight types for recommendations
export type AIInsightType = 'buy' | 'sell' | 'alert';

// AI insight data structure
export interface AIInsight {
  type: AIInsightType;
  symbol?: string;
  text: string;
  confidence?: number;
}

// Portfolio summary data
export interface PortfolioSummary {
  totalValue: number;
  dayChange: number;
  dayChangePercent: number;
}

// Manual trading statistics
export interface ManualTradingStats {
  today: number;
  thisMonth: number;
}

// Auto-trading statistics
export interface AutoTradingStats {
  pnl: number;
  winRate: number;
  lossRatio: number;
  trades: number;
  isActive: boolean;
}

// Activity item for activity feed
export interface ActivityItem {
  icon: React.ComponentType<{ className?: string }>;
  iconColor: string;
  iconBg: string;
  title: string;
  subtitle: string;
  time: string;
  isAutoTrade?: boolean;
}

// Course/Learning content
export interface Course {
  level: 'Beginner' | 'Intermediate' | 'Advanced';
  title: string;
  lessons: number;
  duration: string;
  progress: number;
}

// Financial tool/calculator
export interface FinancialTool {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  desc: string;
}

// Document for statements tab
export interface StatementDocument {
  type: string;
  date: string;
  size: string;
}

// Auto-trading strategy
export interface TradingStrategy {
  name: string;
  status: 'Active' | 'Paused' | 'Stopped';
  pnl: string;
  trades: number;
}

// Contingency item (beneficiaries, trusted contacts, etc.)
export interface ContingencyItem {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  desc: string;
  action: string;
}

// Product/Service enrollment
export interface ProductEnrollment {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  desc: string;
  status: 'Active' | 'Not enrolled';
}

// Color palette constants
export const ELSON_COLORS = {
  primaryGold: '#C9A227',
  primaryGoldLight: '#E8D48B',
  bgDark: '#0D1B2A',
  bgCard: '#1B2838',
  bgInput: '#0a1520',
  bgStat: '#1a2535',
  borderGold: 'rgba(201, 162, 39, 0.1)',
  borderGoldHover: 'rgba(201, 162, 39, 0.3)',
} as const;

// Role styling configuration
export const ROLE_STYLES: Record<FamilyRole, { backgroundColor: string; color: string }> = {
  owner: { backgroundColor: 'rgba(201, 162, 39, 0.2)', color: '#C9A227' },
  adult: { backgroundColor: 'rgba(59, 130, 246, 0.2)', color: '#60A5FA' },
  teen: { backgroundColor: 'rgba(168, 85, 247, 0.2)', color: '#A78BFA' },
  child: { backgroundColor: 'rgba(34, 197, 94, 0.2)', color: '#4ADE80' },
};

// Role labels
export const ROLE_LABELS: Record<FamilyRole, string> = {
  owner: 'You',
  adult: 'Adult',
  teen: 'Teen',
  child: 'Child',
};

// Tier badge styling
export const TIER_STYLES: Record<UserTier, { backgroundColor: string; color: string }> = {
  Starter: { backgroundColor: 'rgba(107, 114, 128, 0.2)', color: '#9CA3AF' },
  Growth: { backgroundColor: 'rgba(59, 130, 246, 0.2)', color: '#60A5FA' },
  Wealth: { backgroundColor: 'rgba(201, 162, 39, 0.2)', color: '#C9A227' },
};

// Course level styling
export const LEVEL_STYLES = {
  Beginner: { backgroundColor: 'rgba(34, 197, 94, 0.2)', color: '#4ADE80' },
  Intermediate: { backgroundColor: 'rgba(59, 130, 246, 0.2)', color: '#60A5FA' },
  Advanced: { backgroundColor: 'rgba(168, 85, 247, 0.2)', color: '#A78BFA' },
} as const;

// Insight type configuration
export const INSIGHT_TYPE_CONFIG = {
  buy: {
    color: '#4ADE80',
    bg: 'rgba(34, 197, 94, 0.2)',
    label: 'BUY'
  },
  sell: {
    color: '#F87171',
    bg: 'rgba(239, 68, 68, 0.2)',
    label: 'SELL'
  },
  alert: {
    color: '#FB923C',
    bg: 'rgba(249, 115, 22, 0.2)',
    label: 'ALERT'
  },
} as const;

// Time period options
export const TIME_PERIODS = ['1D', '1W', '1M', '3M', '1Y', 'ALL'] as const;
export type TimePeriod = typeof TIME_PERIODS[number];
