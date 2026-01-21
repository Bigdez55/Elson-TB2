import React, { useState } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../store/store';
import { Link, useNavigate } from 'react-router-dom';
import { useTradingContext } from '../contexts/TradingContext';
import { useGetBatchDataQuery, useGetPortfolioPerformanceQuery } from '../services/tradingApi';
import { Skeleton } from '../components/common/Skeleton';

// Elson Design Components
import {
  Card,
  CardHeader,
  TabGroup,
  TimePeriodSelector,
  PortfolioChart,
  FamilyMemberRow,
  AIInsightRow,
  ActivityRow,
  PremiumLock,
} from '../components/elson';
import {
  ExclamationCircleIcon,
  ChatIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  AutoTradingIcon,
} from '../components/icons/ElsonIcons';
import { FamilyMember, AIInsight, UserTier, TimePeriod } from '../types/elson';

const DashboardPage: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth);
  const { mode } = useTradingContext();
  const navigate = useNavigate();
  const [timePeriod, setTimePeriod] = useState<TimePeriod>('1W');

  // User tier - would come from subscription data in production
  // Using a function to prevent TypeScript from narrowing the type
  const getUserTier = (): UserTier => 'Growth';
  const userTier = getUserTier();

  // Map timeframe to API period format
  const apiPeriod: '1W' | '1M' | '3M' | '1Y' | 'ALL' =
    timePeriod === 'ALL' ? 'ALL' : timePeriod === '1D' ? '1W' : timePeriod as '1W' | '1M' | '3M' | '1Y';

  // Fetch real portfolio data
  const { data: batchData, isLoading, error } = useGetBatchDataQuery({ mode });
  const { data: performanceData } = useGetPortfolioPerformanceQuery({ mode, period: apiPeriod });

  const portfolio = batchData?.portfolio;
  const positions = batchData?.positions || [];

  // Mock family members for now - would come from API
  const familyMembers: FamilyMember[] = [
    { id: '1', name: 'You', role: 'owner', value: portfolio?.total_value || 0, change: portfolio?.day_pnl_percent || 0 },
  ];

  // Mock AI insights - would come from AI service
  const aiInsights: AIInsight[] = [
    { type: 'buy', symbol: 'NVDA', text: 'Strong momentum with positive sentiment across social and news channels', confidence: 87 },
    { type: 'alert', text: 'Your portfolio is up today - consider taking some profits', confidence: 72 },
  ];

  // Mock activities
  const activities = [
    {
      icon: ArrowUpIcon,
      iconColor: 'text-green-400',
      iconBg: 'rgba(34, 197, 94, 0.2)',
      title: 'Bought AAPL',
      subtitle: '10 shares @ $178.32',
      time: '2h ago',
      isAutoTrade: false,
    },
    {
      icon: ArrowDownIcon,
      iconColor: 'text-red-400',
      iconBg: 'rgba(239, 68, 68, 0.2)',
      title: 'Sold MSFT',
      subtitle: '5 shares @ $421.50',
      time: '4h ago',
      isAutoTrade: true,
    },
  ];

  const isNotStarterTier = (tier: UserTier): boolean => tier !== 'Starter';
  const showFamily = isNotStarterTier(userTier);
  const showAutoTrading = isNotStarterTier(userTier);
  const canTrade = isNotStarterTier(userTier);

  // Calculate trading stats from positions
  const dayPnl = portfolio?.day_pnl || 0;
  const totalPnl = portfolio?.total_pnl || 0;

  const manualTradingStats = {
    today: dayPnl,
    thisMonth: totalPnl,
  };

  const autoTradingStats = {
    pnl: 2847,
    winRate: 68,
    lossRatio: 0.42,
    trades: 47,
    isActive: true,
  };

  if (isLoading) {
    return (
      <div className="min-h-screen p-6" style={{ backgroundColor: '#0D1B2A' }}>
        <div className="space-y-4">
          <Skeleton variant="text" width={250} height={28} />
          <Skeleton variant="rectangular" width="100%" height={300} className="rounded-2xl" />
          <div className="grid grid-cols-2 gap-4">
            <Skeleton variant="rectangular" width="100%" height={150} className="rounded-2xl" />
            <Skeleton variant="rectangular" width="100%" height={150} className="rounded-2xl" />
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen p-6" style={{ backgroundColor: '#0D1B2A' }}>
        <div className="bg-red-900/30 border border-red-500 rounded-xl p-4 text-red-300">
          Failed to load portfolio data. Please try again later.
        </div>
      </div>
    );
  }

  const totalValue = portfolio?.total_value || 0;
  const dayChange = portfolio?.day_pnl || 0;
  const dayChangePercent = portfolio?.day_pnl_percent || 0;

  return (
    <div className="min-h-screen p-4 md:p-6 space-y-4 md:space-y-6" style={{ backgroundColor: '#0D1B2A' }}>
      {/* Family Overview Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1">
            {showFamily ? 'Family Overview' : `Welcome back, ${user?.full_name?.split(' ')[0] || 'there'}`}
          </h1>
          <p className="text-gray-400 text-sm">
            {showFamily
              ? `${familyMembers.length} family member${familyMembers.length > 1 ? 's' : ''} · $${totalValue.toLocaleString()} total`
              : `Here's your portfolio summary for ${mode === 'paper' ? 'paper trading' : 'live trading'}.`
            }
          </p>
        </div>
        {mode === 'paper' && (
          <span
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-blue-400 text-sm font-medium"
            style={{ backgroundColor: 'rgba(59, 130, 246, 0.2)' }}
          >
            Paper Trading Mode
          </span>
        )}
      </div>

      {/* Portfolio Value Card */}
      <Card className="p-4 md:p-6">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-4">
          <div>
            <p className="text-gray-400 text-sm font-medium mb-1">Total Portfolio Value</p>
            <h2 className="font-serif text-3xl md:text-4xl xl:text-5xl font-bold text-white mb-2">
              ${totalValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </h2>
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`text-base md:text-lg font-semibold ${dayChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {dayChange >= 0 ? '+' : ''}${Math.abs(dayChange).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </span>
              <span className={`text-sm ${dayChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                ({dayChange >= 0 ? '+' : ''}{dayChangePercent.toFixed(2)}%)
              </span>
              <span className="text-gray-500 text-sm">Today</span>
            </div>
          </div>
          <div className="flex gap-2 md:gap-3">
            <button
              onClick={() => navigate(`/${mode}/trading`)}
              className="flex-1 md:flex-none px-5 py-3 rounded-xl font-semibold text-[#0D1B2A] hover:shadow-lg hover:shadow-[#C9A227]/20 transition-all"
              style={{ background: 'linear-gradient(to right, #C9A227, #E8D48B)' }}
            >
              Buy
            </button>
            <button
              onClick={() => navigate(`/${mode}/trading`)}
              className="flex-1 md:flex-none px-5 py-3 rounded-xl font-semibold text-[#C9A227] hover:bg-[#C9A227]/25 transition-all"
              style={{ backgroundColor: 'rgba(201, 162, 39, 0.15)', border: '1px solid rgba(201, 162, 39, 0.3)' }}
            >
              Sell
            </button>
            <button
              onClick={() => navigate('/transfers')}
              className="flex-1 md:flex-none px-5 py-3 rounded-xl font-semibold text-[#C9A227] hover:bg-[#C9A227]/25 transition-all"
              style={{ backgroundColor: 'rgba(201, 162, 39, 0.15)', border: '1px solid rgba(201, 162, 39, 0.3)' }}
            >
              Transfer
            </button>
          </div>
        </div>
        <TimePeriodSelector value={timePeriod} onChange={setTimePeriod} />
        <PortfolioChart />
      </Card>

      {/* Trading Stats Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Manual Trading */}
        <Card className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">Manual Trading</h3>
            <span className="text-xs text-gray-500">Your trades</span>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className={`text-xl font-semibold ${manualTradingStats.today >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {manualTradingStats.today >= 0 ? '+' : ''}${Math.abs(manualTradingStats.today).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </p>
              <p className="text-xs text-gray-500">Today</p>
            </div>
            <div>
              <p className={`text-xl font-semibold ${manualTradingStats.thisMonth >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {manualTradingStats.thisMonth >= 0 ? '+' : ''}${Math.abs(manualTradingStats.thisMonth).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </p>
              <p className="text-xs text-gray-500">Total P&L</p>
            </div>
          </div>
        </Card>

        {/* Auto-Trading */}
        {showAutoTrading ? (
          <Card className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">Auto-Trading</h3>
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${autoTradingStats.isActive ? 'bg-green-500 animate-pulse' : 'bg-gray-500'}`} />
                <span className={`text-xs font-medium ${autoTradingStats.isActive ? 'text-green-400' : 'text-gray-500'}`}>
                  {autoTradingStats.isActive ? 'Active' : 'Paused'}
                </span>
              </div>
            </div>
            <div className="grid grid-cols-4 gap-3">
              <div>
                <p className={`text-lg font-semibold ${autoTradingStats.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {autoTradingStats.pnl >= 0 ? '+' : ''}${Math.abs(autoTradingStats.pnl).toLocaleString()}
                </p>
                <p className="text-xs text-gray-500">P&L</p>
              </div>
              <div>
                <p className="text-lg font-semibold text-white">{autoTradingStats.winRate}%</p>
                <p className="text-xs text-gray-500">Win Rate</p>
              </div>
              <div>
                <p className="text-lg font-semibold text-white">{autoTradingStats.lossRatio}</p>
                <p className="text-xs text-gray-500">Loss Ratio</p>
              </div>
              <div>
                <p className="text-lg font-semibold text-white">{autoTradingStats.trades}</p>
                <p className="text-xs text-gray-500">Trades</p>
              </div>
            </div>
            <button
              onClick={() => navigate('/settings')}
              className="w-full mt-4 py-2 rounded-lg text-[#C9A227] text-sm font-medium hover:bg-[#C9A227]/20 transition-colors"
              style={{ backgroundColor: 'rgba(201, 162, 39, 0.1)', border: '1px solid rgba(201, 162, 39, 0.3)' }}
            >
              View Auto-Trading Details
            </button>
          </Card>
        ) : (
          <PremiumLock feature="Auto-Trading" requiredTier="Growth" onUpgrade={() => navigate('/pricing')}>
            <Card className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">Auto-Trading</h3>
              </div>
              <div className="grid grid-cols-4 gap-3">
                <div>
                  <p className="text-lg font-semibold text-green-400">+$2,847</p>
                  <p className="text-xs text-gray-500">P&L</p>
                </div>
                <div>
                  <p className="text-lg font-semibold text-white">68%</p>
                  <p className="text-xs text-gray-500">Win Rate</p>
                </div>
                <div>
                  <p className="text-lg font-semibold text-white">0.42</p>
                  <p className="text-xs text-gray-500">Loss Ratio</p>
                </div>
                <div>
                  <p className="text-lg font-semibold text-white">12</p>
                  <p className="text-xs text-gray-500">Trades</p>
                </div>
              </div>
            </Card>
          </PremiumLock>
        )}
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-4 md:gap-6">
        {/* Family Accounts / Holdings */}
        {showFamily && familyMembers.length > 1 ? (
          <Card className="xl:col-span-4">
            <CardHeader title="Family Accounts" badge={`${familyMembers.length} members`} action={() => navigate('/family')} actionLabel="Manage" />
            <div>
              {familyMembers.map((member) => (
                <FamilyMemberRow
                  key={member.id}
                  member={member}
                  canTrade={canTrade}
                  onTrade={() => navigate(`/${mode}/trading`)}
                  onView={() => navigate('/family')}
                />
              ))}
            </div>
          </Card>
        ) : (
          <Card className="xl:col-span-4">
            <CardHeader title="Your Positions" badge={`${positions.length} holdings`} action={() => navigate('/portfolio')} />
            <div className="divide-y divide-gray-800/50">
              {positions.length === 0 ? (
                <div className="p-4 text-center text-gray-400">
                  <p className="mb-2">No positions yet</p>
                  <Link to={`/${mode}/trading`} className="text-[#C9A227] hover:underline text-sm">
                    Start Trading →
                  </Link>
                </div>
              ) : (
                positions.slice(0, 4).map((position) => (
                  <div
                    key={position.id}
                    className="flex items-center p-3 hover:bg-[#1B2838]/30 transition-all"
                  >
                    <div
                      className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#C9A227]/30 to-[#C9A227]/10 flex items-center justify-center text-[#C9A227] text-xs font-bold flex-shrink-0"
                    >
                      {position.symbol.slice(0, 2)}
                    </div>
                    <div className="flex-1 ml-3 min-w-0">
                      <p className="text-sm font-medium text-white truncate">{position.symbol}</p>
                      <p className="text-xs text-gray-500">{position.quantity.toFixed(4)} shares</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-white">${position.market_value.toFixed(2)}</p>
                      <p className={`text-xs ${(position.unrealized_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {(position.unrealized_pnl || 0) >= 0 ? '+' : ''}{(position.unrealized_pnl_percent || 0).toFixed(2)}%
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        )}

        {/* AI Insights */}
        <Card className="xl:col-span-4">
          <CardHeader title="Elson AI Insights" action={() => navigate('/ai')} actionLabel="View All" />
          <div className="p-4 space-y-3">
            {userTier === 'Starter' ? (
              <>
                {aiInsights.slice(0, 1).map((insight, i) => (
                  <AIInsightRow key={i} insight={insight} />
                ))}
                <div
                  className="p-3 rounded-lg text-center"
                  style={{ backgroundColor: '#1a2535', border: '1px dashed #374151' }}
                >
                  <p className="text-sm text-gray-400 mb-2">2 of 3 daily insights remaining</p>
                  <button
                    onClick={() => navigate('/pricing')}
                    className="text-[#C9A227] text-sm font-medium hover:underline"
                  >
                    Upgrade for unlimited
                  </button>
                </div>
              </>
            ) : (
              aiInsights.map((insight, i) => (
                <AIInsightRow key={i} insight={insight} />
              ))
            )}
          </div>
          <div className="p-4 pt-0">
            <button
              onClick={() => navigate('/ai')}
              className="w-full py-3 rounded-xl text-[#C9A227] text-sm font-semibold hover:bg-[#C9A227]/30 transition-all flex items-center justify-center gap-2"
              style={{ background: 'linear-gradient(to right, rgba(201, 162, 39, 0.2), rgba(232, 212, 139, 0.2))', border: '1px solid rgba(201, 162, 39, 0.3)' }}
            >
              <ChatIcon className="w-4 h-4" />
              Ask Elson AI
            </button>
          </div>
        </Card>

        {/* Activity */}
        <Card className="xl:col-span-4">
          <CardHeader title="Recent Activity" action={() => navigate('/portfolio')} />
          <div className="p-4">
            {activities.length === 0 ? (
              <p className="text-center text-gray-400 py-4">No recent activity</p>
            ) : (
              activities.map((activity, i) => (
                <ActivityRow key={i} {...activity} />
              ))
            )}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default DashboardPage;
