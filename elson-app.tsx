import React, { useState } from 'react';
 
// ============================================
// ICON COMPONENTS
// ============================================
const Icons = {
  Search: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
    </svg>
  ),
  Bell: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
    </svg>
  ),
  Help: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
    </svg>
  ),
  Dashboard: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z"/>
    </svg>
  ),
  AI: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
    </svg>
  ),
  Invest: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
    </svg>
  ),
  Learn: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
    </svg>
  ),
  Account: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
    </svg>
  ),
  Portfolio: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
    </svg>
  ),
  Discover: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
    </svg>
  ),
  Trending: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
    </svg>
  ),
  History: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
    </svg>
  ),
  Transfer: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"/>
    </svg>
  ),
  Cash: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
    </svg>
  ),
  Stocks: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
    </svg>
  ),
  AutoTrading: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
    </svg>
  ),
  Settings: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
    </svg>
  ),
  Plus: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
    </svg>
  ),
  ArrowUp: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 10l7-7m0 0l7 7m-7-7v18"/>
    </svg>
  ),
  ArrowDown: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 14l-7 7m0 0l-7-7m7 7V3"/>
    </svg>
  ),
  Clock: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
    </svg>
  ),
  User: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
    </svg>
  ),
  Users: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/>
    </svg>
  ),
  Shield: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
    </svg>
  ),
  Document: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
    </svg>
  ),
  Chat: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
    </svg>
  ),
  Lightbulb: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
    </svg>
  ),
  ChartBar: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
    </svg>
  ),
  Target: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"/>
    </svg>
  ),
  Lock: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
    </svg>
  ),
  CheckCircle: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
    </svg>
  ),
  ExclamationCircle: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
    </svg>
  ),
  Logo: ({ className }: { className?: string }) => (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
    </svg>
  ),
  ChevronDown: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"/>
    </svg>
  ),
  Send: ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
    </svg>
  ),
};
 
// ============================================
// TYPES
// ============================================
type UserTier = 'Starter' | 'Growth' | 'Wealth';
type TradingMode = 'Paper' | 'Live';
type ActivePage = 'Dashboard' | 'Elson AI' | 'Invest' | 'Learn' | 'Account';
type FamilyRole = 'owner' | 'adult' | 'teen' | 'child';
 
interface FamilyMember {
  id: string;
  name: string;
  role: FamilyRole;
  value: number;
  change: number;
  pendingApprovals?: number;
}
 
interface Holding {
  symbol: string;
  name: string;
  shares: string;
  value: string;
  change: number;
  color: string;
}
 
interface AIInsight {
  type: 'buy' | 'sell' | 'alert';
  symbol?: string;
  text: string;
  confidence?: number;
}
 
// ============================================
// REUSABLE COMPONENTS
// ============================================
 
// Market Status Strip
const MarketStatusStrip = () => {
  const isOpen = true;
  const timeToClose = '2h 34m';
 
  return (
    <div className="flex items-center justify-center gap-2 py-1.5" style={{ backgroundColor: '#050A0F', borderBottom: '1px solid rgba(55, 65, 81, 0.3)' }}>
      <span className={`w-1.5 h-1.5 rounded-full ${isOpen ? 'bg-green-500' : 'bg-red-500'}`} />
      <span className="text-xs text-gray-400">
        Market {isOpen ? 'Open' : 'Closed'} · {isOpen ? `Closes in ${timeToClose}` : 'Opens in 14h 23m'}
      </span>
    </div>
  );
};
 
// Toggle Button Group
const ToggleGroup = ({
  options,
  value,
  onChange,
  size = 'default'
}: {
  options: string[];
  value: string;
  onChange: (val: string) => void;
  size?: 'small' | 'default';
}) => {
  const sizeClasses = size === 'small'
    ? 'text-xs px-3 py-2 min-h-[36px]'
    : 'text-sm px-4 py-2.5 min-h-[44px]';
 
  return (
    <div className="flex rounded-lg p-1" style={{ backgroundColor: '#050A0F' }}>
      {options.map((option) => (
        <button
          key={option}
          onClick={() => onChange(option)}
          className={`${sizeClasses} flex-1 rounded-lg font-semibold transition-all ${
            value === option
              ? 'text-[#0D1B2A]'
              : 'text-gray-500 hover:text-gray-300'
          }`}
          style={value === option ? { background: 'linear-gradient(to right, #C9A227, #E8D48B)' } : {}}
        >
          {option}
        </button>
      ))}
    </div>
  );
};
 
// Tab Group
const TabGroup = ({
  tabs,
  value,
  onChange
}: {
  tabs: string[];
  value: string;
  onChange: (val: string) => void;
}) => (
  <div className="flex gap-1 overflow-x-auto pb-2 -mx-4 px-4 md:mx-0 md:px-0">
    {tabs.map((tab) => (
      <button
        key={tab}
        onClick={() => onChange(tab)}
        className={`px-4 py-2 rounded-lg text-sm font-medium min-h-[40px] whitespace-nowrap transition-all ${
          value === tab
            ? 'text-[#C9A227]'
            : 'text-gray-400 hover:text-gray-200'
        }`}
        style={value === tab ? { backgroundColor: 'rgba(201, 162, 39, 0.2)', border: '1px solid rgba(201, 162, 39, 0.3)' } : {}}
      >
        {tab}
      </button>
    ))}
  </div>
);
 
// Card Component
const Card = ({
  children,
  className = '',
  hover = true
}: {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
}) => (
  <div 
    className={`rounded-2xl transition-all ${hover ? 'hover:border-[#C9A227]/25' : ''} ${className}`}
    style={{ backgroundColor: '#1B2838', border: '1px solid rgba(201, 162, 39, 0.1)' }}
  >
    {children}
  </div>
);
 
// Card Header
const CardHeader = ({
  title,
  action,
  actionLabel = 'View All',
  badge
}: {
  title: string;
  action?: () => void;
  actionLabel?: string;
  badge?: string;
}) => (
  <div className="flex items-center justify-between p-4 border-b border-gray-800/50">
    <div className="flex items-center gap-2">
      <h2 className="text-base font-semibold text-white">{title}</h2>
      {badge && (
        <span 
          className="px-2 py-0.5 rounded-full text-[#C9A227] text-xs font-medium"
          style={{ backgroundColor: 'rgba(201, 162, 39, 0.2)' }}
        >
          {badge}
        </span>
      )}
    </div>
    {action && (
      <button onClick={action} className="text-[#C9A227] text-sm font-medium hover:underline">
        {actionLabel}
      </button>
    )}
  </div>
);
 
// Stat Card
const StatCard = ({
  icon: Icon,
  label,
  value,
  subtext,
  valueColor = 'text-white'
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  subtext: string;
  valueColor?: string;
}) => (
  <div 
    className="rounded-xl p-4 hover:border-[#C9A227]/30 transition-all"
    style={{ backgroundColor: '#1a2535', border: '1px solid rgba(201, 162, 39, 0.1)' }}
  >
    <div className="flex items-center gap-3 mb-2">
      <div 
        className="w-10 h-10 rounded-xl flex items-center justify-center"
        style={{ background: 'linear-gradient(to bottom right, rgba(201, 162, 39, 0.2), rgba(201, 162, 39, 0.1))' }}
      >
        <Icon className="w-4 h-4 text-[#C9A227]" />
      </div>
    </div>
    <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">{label}</p>
    <p className={`text-lg font-semibold ${valueColor}`}>{value}</p>
    <p className="text-xs text-gray-500">{subtext}</p>
  </div>
);
 
// Tier Badge
const TierBadge = ({ tier }: { tier: UserTier }) => {
  const styles = {
    Starter: { backgroundColor: 'rgba(107, 114, 128, 0.2)', color: '#9CA3AF' },
    Growth: { backgroundColor: 'rgba(59, 130, 246, 0.2)', color: '#60A5FA' },
    Wealth: { backgroundColor: 'rgba(201, 162, 39, 0.2)', color: '#C9A227' },
  };
 
  return (
    <span 
      className="px-2 py-0.5 rounded-full text-xs font-medium"
      style={styles[tier]}
    >
      {tier}
    </span>
  );
};
 
// Premium Feature Lock
const PremiumLock = ({
  feature,
  requiredTier = 'Growth',
  children
}: {
  feature: string;
  requiredTier?: UserTier;
  children?: React.ReactNode;
}) => (
  <div className="relative">
    <div 
      className="absolute inset-0 rounded-xl flex flex-col items-center justify-center z-10"
      style={{ backgroundColor: 'rgba(13, 27, 42, 0.9)' }}
    >
      <Icons.Lock className="w-8 h-8 text-gray-500 mb-2" />
      <p className="text-sm text-gray-400 mb-1">{feature}</p>
      <p className="text-xs text-gray-500 mb-3">Requires {requiredTier} tier</p>
      <button 
        className="px-4 py-2 rounded-lg text-[#0D1B2A] text-sm font-semibold"
        style={{ background: 'linear-gradient(to right, #C9A227, #E8D48B)' }}
      >
        Upgrade
      </button>
    </div>
    <div className="opacity-30 pointer-events-none">
      {children}
    </div>
  </div>
);
 
// Family Member Row
const FamilyMemberRow = ({
  member,
  onTrade,
  onView,
  canTrade = true
}: {
  member: FamilyMember;
  onTrade?: () => void;
  onView?: () => void;
  canTrade?: boolean;
}) => {
  const roleStyles = {
    owner: { backgroundColor: 'rgba(201, 162, 39, 0.2)', color: '#C9A227' },
    adult: { backgroundColor: 'rgba(59, 130, 246, 0.2)', color: '#60A5FA' },
    teen: { backgroundColor: 'rgba(168, 85, 247, 0.2)', color: '#A78BFA' },
    child: { backgroundColor: 'rgba(34, 197, 94, 0.2)', color: '#4ADE80' },
  };
 
  const roleLabels = {
    owner: 'You',
    adult: 'Adult',
    teen: 'Teen',
    child: 'Child',
  };
 
  return (
    <div 
      className="flex items-center p-3 last:border-b-0 hover:bg-[#1B2838]/30 transition-all"
      style={{ borderBottom: '1px solid rgba(55, 65, 81, 0.3)' }}
    >
      <div 
        className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
        style={{ background: 'linear-gradient(to bottom right, rgba(201, 162, 39, 0.3), rgba(201, 162, 39, 0.1))' }}
      >
        <span className="text-[#C9A227] text-sm font-bold">{member.name[0]}</span>
      </div>
      <div className="flex-1 ml-3 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium text-white truncate">{member.name}</p>
          <span 
            className="px-1.5 py-0.5 rounded text-[10px] font-medium"
            style={roleStyles[member.role]}
          >
            {roleLabels[member.role]}
          </span>
        </div>
        <p className="text-xs text-gray-500">
          ${member.value.toLocaleString()}
          <span className={member.change >= 0 ? 'text-green-400' : 'text-red-400'}>
            {' '}({member.change >= 0 ? '+' : ''}{member.change}%)
          </span>
        </p>
      </div>
      <div className="flex items-center gap-2">
        {member.pendingApprovals && member.pendingApprovals > 0 && (
          <span 
            className="px-2 py-1 rounded-full text-orange-400 text-xs font-medium"
            style={{ backgroundColor: 'rgba(249, 115, 22, 0.2)' }}
          >
            {member.pendingApprovals} pending
          </span>
        )}
        {canTrade && member.role !== 'child' ? (
          <button
            onClick={onTrade}
            className="px-3 py-1.5 rounded-lg text-[#C9A227] text-xs font-medium hover:bg-[#C9A227]/20 transition-colors"
            style={{ backgroundColor: 'rgba(201, 162, 39, 0.1)' }}
          >
            Trade
          </button>
        ) : (
          <button
            onClick={onView}
            className="px-3 py-1.5 rounded-lg text-gray-400 text-xs font-medium hover:bg-gray-500/20 transition-colors"
            style={{ backgroundColor: 'rgba(107, 114, 128, 0.1)' }}
          >
            View
          </button>
        )}
      </div>
    </div>
  );
};
 
// AI Insight Row
const AIInsightRow = ({ insight }: { insight: AIInsight }) => {
  const typeConfig = {
    buy: { icon: Icons.ArrowUp, color: '#4ADE80', bg: 'rgba(34, 197, 94, 0.2)', label: 'BUY' },
    sell: { icon: Icons.ArrowDown, color: '#F87171', bg: 'rgba(239, 68, 68, 0.2)', label: 'SELL' },
    alert: { icon: Icons.ExclamationCircle, color: '#FB923C', bg: 'rgba(249, 115, 22, 0.2)', label: 'ALERT' },
  };
 
  const config = typeConfig[insight.type];
  const Icon = config.icon;
 
  return (
    <div 
      className="flex items-start gap-3 p-3 rounded-lg transition-all"
      style={{ backgroundColor: '#1a2535' }}
    >
      <div 
        className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
        style={{ backgroundColor: config.bg }}
      >
        <Icon className="w-4 h-4" style={{ color: config.color }} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-bold" style={{ color: config.color }}>{config.label}</span>
          {insight.symbol && (
            <span className="text-sm font-semibold text-white">{insight.symbol}</span>
          )}
          {insight.confidence && (
            <span className="text-xs text-gray-500">{insight.confidence}% confidence</span>
          )}
        </div>
        <p className="text-sm text-gray-400">{insight.text}</p>
      </div>
    </div>
  );
};
 
// Holding Row
const HoldingRow = ({
  symbol,
  name,
  shares,
  value,
  change,
  color
}: Holding) => (
  <a 
    href="#" 
    className="flex items-center p-4 hover:bg-[#1B2838]/30 transition-all min-h-[72px] last:border-b-0"
    style={{ borderBottom: '1px solid rgba(55, 65, 81, 0.3)' }}
  >
    <div className={`w-10 h-10 rounded-lg ${color} flex items-center justify-center text-white text-xs font-bold flex-shrink-0`}>
      {symbol.slice(0, 2)}
    </div>
    <div className="flex-1 ml-3 min-w-0">
      <p className="text-sm font-medium text-white truncate">{name}</p>
      <p className="text-xs text-gray-500">{shares}</p>
    </div>
    <div className="text-right">
      <p className="text-sm font-medium text-white">{value}</p>
      <p className={`text-xs ${change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
        {change >= 0 ? '+' : ''}{change}%
      </p>
    </div>
  </a>
);
 
// Activity Row
const ActivityRow = ({
  icon: Icon,
  iconColor,
  iconBg,
  title,
  subtitle,
  time,
  isAutoTrade = false
}: {
  icon: React.ComponentType<{ className?: string }>;
  iconColor: string;
  iconBg: string;
  title: string;
  subtitle: string;
  time: string;
  isAutoTrade?: boolean;
}) => (
  <div 
    className="flex items-center gap-3 py-3 last:border-b-0"
    style={{ borderBottom: '1px solid rgba(55, 65, 81, 0.3)' }}
  >
    <div 
      className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0"
      style={{ backgroundColor: iconBg }}
    >
      <Icon className={`w-4 h-4 ${iconColor}`} />
    </div>
    <div className="flex-1 min-w-0">
      <div className="flex items-center gap-2">
        <p className="text-sm font-medium text-white">{title}</p>
        {isAutoTrade && (
          <span 
            className="px-1.5 py-0.5 rounded text-[10px] font-medium text-blue-400"
            style={{ backgroundColor: 'rgba(59, 130, 246, 0.2)' }}
          >
            AUTO
          </span>
        )}
      </div>
      <p className="text-xs text-gray-500">{subtitle}</p>
    </div>
    <p className="text-xs text-gray-500">{time}</p>
  </div>
);
 
// Sidebar Nav Item
const SidebarItem = ({
  icon: Icon,
  label,
  active = false,
  onClick,
  badge
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  active?: boolean;
  onClick?: () => void;
  badge?: number;
}) => (
  <button
    onClick={onClick}
    className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all min-h-[44px] ${
      active
        ? 'text-[#C9A227]'
        : 'text-gray-400 hover:bg-[#C9A227]/10 hover:text-gray-200'
    }`}
    style={active ? { backgroundColor: 'rgba(201, 162, 39, 0.15)', borderLeft: '3px solid #C9A227', marginLeft: '-3px' } : {}}
  >
    <Icon className="w-5 h-5" />
    <span className="flex-1 text-left">{label}</span>
    {badge && badge > 0 && (
      <span 
        className="px-2 py-0.5 rounded-full text-[#C9A227] text-xs font-medium"
        style={{ backgroundColor: 'rgba(201, 162, 39, 0.2)' }}
      >
        {badge}
      </span>
    )}
  </button>
);
 
// Bottom Nav Item
const BottomNavItem = ({
  icon: Icon,
  label,
  active = false,
  onClick
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  active?: boolean;
  onClick?: () => void;
}) => (
  <button
    onClick={onClick}
    className={`flex flex-col items-center justify-center gap-1 min-h-[48px] min-w-[64px] px-3 py-2 rounded-xl transition-all ${
      active ? 'text-[#C9A227]' : 'text-gray-500'
    }`}
  >
    <Icon className="w-6 h-6" />
    <span className="text-[11px] font-medium">{label}</span>
  </button>
);
 
// Portfolio Chart
const PortfolioChart = () => (
  <div className="h-[200px] lg:h-[240px] relative overflow-hidden">
    <svg width="100%" height="100%" viewBox="0 0 800 240" preserveAspectRatio="none">
      <defs>
        <linearGradient id="goldGradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="rgba(201, 162, 39, 0.3)"/>
          <stop offset="100%" stopColor="rgba(201, 162, 39, 0)"/>
        </linearGradient>
      </defs>
      <g stroke="rgba(255,255,255,0.05)" strokeWidth="1">
        <line x1="0" y1="60" x2="800" y2="60"/>
        <line x1="0" y1="120" x2="800" y2="120"/>
        <line x1="0" y1="180" x2="800" y2="180"/>
      </g>
      <path fill="url(#goldGradient)" d="M0,180 Q100,160 200,130 T400,100 T600,70 T800,80 L800,240 L0,240 Z"/>
      <path fill="none" stroke="#C9A227" strokeWidth="2" d="M0,180 Q100,160 200,130 T400,100 T600,70 T800,80"/>
      <circle cx="200" cy="130" r="4" fill="#C9A227"/>
      <circle cx="400" cy="100" r="4" fill="#C9A227"/>
      <circle cx="600" cy="70" r="4" fill="#C9A227"/>
      <circle cx="800" cy="80" r="4" fill="#C9A227"/>
    </svg>
  </div>
);
 
// Time Period Selector
const TimePeriodSelector = ({
  value,
  onChange
}: {
  value: string;
  onChange: (val: string) => void;
}) => {
  const periods = ['1D', '1W', '1M', '3M', '1Y', 'ALL'];
 
  return (
    <div className="flex items-center gap-1 overflow-x-auto pb-2 -mx-4 px-4 md:mx-0 md:px-0">
      {periods.map((period) => (
        <button
          key={period}
          onClick={() => onChange(period)}
          className={`px-3 py-2 rounded-lg text-xs font-semibold min-h-[36px] min-w-[44px] transition-all flex-shrink-0 ${
            value === period
              ? 'text-[#C9A227]'
              : 'text-gray-500 hover:text-gray-300'
          }`}
          style={value === period ? { backgroundColor: 'rgba(201, 162, 39, 0.2)' } : {}}
        >
          {period}
        </button>
      ))}
    </div>
  );
};
 
// ============================================
// PAGE COMPONENTS
// ============================================
 
// Dashboard Page
const DashboardPage = ({
  userTier,
  tradingMode,
  familyMembers,
  portfolio,
  manualTradingStats,
  autoTradingStats,
  aiInsights,
  activities,
  pendingApprovals
}: {
  userTier: UserTier;
  tradingMode: TradingMode;
  familyMembers: FamilyMember[];
  portfolio: { totalValue: number; dayChange: number; dayChangePercent: number };
  manualTradingStats: { today: number; thisMonth: number };
  autoTradingStats: { pnl: number; winRate: number; lossRatio: number; trades: number; isActive: boolean };
  aiInsights: AIInsight[];
  activities: any[];
  pendingApprovals: number;
}) => {
  const [timePeriod, setTimePeriod] = useState('1W');
  const showFamily = userTier !== 'Starter';
  const showAutoTrading = userTier !== 'Starter';
 
  return (
    <div className="space-y-4 md:space-y-6" style={{ backgroundColor: '#0D1B2A' }}>
      {/* Family Overview Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1">
            {showFamily ? 'Family Overview' : 'Your Portfolio'}
          </h1>
          <p className="text-gray-400 text-sm">
            {showFamily
              ? `${familyMembers.length} family members · $${portfolio.totalValue.toLocaleString()} total`
              : `Welcome back! Here's your portfolio summary.`
            }
          </p>
        </div>
        {pendingApprovals > 0 && (
          <button 
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-orange-400 text-sm font-medium"
            style={{ backgroundColor: 'rgba(249, 115, 22, 0.2)' }}
          >
            <Icons.ExclamationCircle className="w-4 h-4" />
            {pendingApprovals} Pending Approval{pendingApprovals > 1 ? 's' : ''}
          </button>
        )}
      </div>
 
      {/* Portfolio Value Card */}
      <Card className="p-4 md:p-6">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-4">
          <div>
            <p className="text-gray-400 text-sm font-medium mb-1">Total Portfolio Value</p>
            <h2 className="font-serif text-3xl md:text-4xl xl:text-5xl font-bold text-white mb-2">
              ${portfolio.totalValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </h2>
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`text-base md:text-lg font-semibold ${portfolio.dayChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {portfolio.dayChange >= 0 ? '+' : ''}${Math.abs(portfolio.dayChange).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </span>
              <span className={`text-sm ${portfolio.dayChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                ({portfolio.dayChange >= 0 ? '+' : ''}{portfolio.dayChangePercent}%)
              </span>
              <span className="text-gray-500 text-sm">Today</span>
            </div>
          </div>
          <div className="flex gap-2 md:gap-3">
            <button 
              className="flex-1 md:flex-none px-5 py-3 rounded-xl font-semibold text-[#0D1B2A] hover:shadow-lg hover:shadow-[#C9A227]/20 transition-all"
              style={{ background: 'linear-gradient(to right, #C9A227, #E8D48B)' }}
            >
              Buy
            </button>
            <button 
              className="flex-1 md:flex-none px-5 py-3 rounded-xl font-semibold text-[#C9A227] hover:bg-[#C9A227]/25 transition-all"
              style={{ backgroundColor: 'rgba(201, 162, 39, 0.15)', border: '1px solid rgba(201, 162, 39, 0.3)' }}
            >
              Sell
            </button>
            <button 
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
                {manualTradingStats.today >= 0 ? '+' : ''}${Math.abs(manualTradingStats.today).toLocaleString()}
              </p>
              <p className="text-xs text-gray-500">Today</p>
            </div>
            <div>
              <p className={`text-xl font-semibold ${manualTradingStats.thisMonth >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {manualTradingStats.thisMonth >= 0 ? '+' : ''}${Math.abs(manualTradingStats.thisMonth).toLocaleString()}
              </p>
              <p className="text-xs text-gray-500">This Month</p>
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
              className="w-full mt-4 py-2 rounded-lg text-[#C9A227] text-sm font-medium hover:bg-[#C9A227]/20 transition-colors"
              style={{ backgroundColor: 'rgba(201, 162, 39, 0.1)', border: '1px solid rgba(201, 162, 39, 0.3)' }}
            >
              View Auto-Trading Details
            </button>
          </Card>
        ) : (
          <PremiumLock feature="Auto-Trading" requiredTier="Growth">
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
        {/* Family Accounts */}
        {showFamily && (
          <Card className="xl:col-span-4">
            <CardHeader title="Family Accounts" badge={`${familyMembers.length} members`} action={() => {}} actionLabel="Manage" />
            <div>
              {familyMembers.map((member) => (
                <FamilyMemberRow
                  key={member.id}
                  member={member}
                  canTrade={userTier !== 'Starter'}
                />
              ))}
            </div>
          </Card>
        )}
 
        {/* AI Insights */}
        <Card className={showFamily ? "xl:col-span-4" : "xl:col-span-6"}>
          <CardHeader title="Elson AI Insights" action={() => {}} actionLabel="View All" />
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
                  <button className="text-[#C9A227] text-sm font-medium hover:underline">
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
              className="w-full py-3 rounded-xl text-[#C9A227] text-sm font-semibold hover:bg-[#C9A227]/30 transition-all flex items-center justify-center gap-2"
              style={{ background: 'linear-gradient(to right, rgba(201, 162, 39, 0.2), rgba(232, 212, 139, 0.2))', border: '1px solid rgba(201, 162, 39, 0.3)' }}
            >
              <Icons.Chat className="w-4 h-4" />
              Ask Elson AI
            </button>
          </div>
        </Card>
 
        {/* Activity */}
        <Card className={showFamily ? "xl:col-span-4" : "xl:col-span-6"}>
          <CardHeader title="Recent Activity" action={() => {}} />
          <div className="p-4">
            {activities.map((activity, i) => (
              <ActivityRow key={i} {...activity} />
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};
 
// Elson AI Page
const ElsonAIPage = ({ userTier }: { userTier: UserTier }) => {
  const [activeTab, setActiveTab] = useState('Chat');
  const [message, setMessage] = useState('');
  const tabs = ['Chat', 'Planning', 'Insights', 'Signals', 'Settings'];
 
  const quickPrompts = [
    "How should I prepare for retirement?",
    "Analyze my portfolio risk",
    "What stocks should I consider?",
    "Help me reduce my tax burden",
  ];
 
  return (
    <div className="space-y-4 md:space-y-6" style={{ backgroundColor: '#0D1B2A' }}>
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Elson AI</h1>
        <p className="text-gray-400 text-sm">Your personal AI financial advisor</p>
      </div>
 
      <TabGroup tabs={tabs} value={activeTab} onChange={setActiveTab} />
 
      {activeTab === 'Chat' && (
        <Card className="min-h-[500px] flex flex-col">
          {/* Chat Messages Area */}
          <div className="flex-1 p-4 space-y-4 overflow-y-auto">
            {/* Welcome Message */}
            <div className="flex gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#C9A227] to-[#E8D48B] flex items-center justify-center flex-shrink-0">
                <Icons.AI className="w-5 h-5 text-[#0D1B2A]" />
              </div>
              <div className="flex-1">
                <p className="text-sm text-gray-400 mb-1">Elson AI</p>
                <div 
                  className="rounded-2xl rounded-tl-none p-4"
                  style={{ backgroundColor: '#1a2535' }}
                >
                  <p className="text-white">
                    Hello! I'm Elson, your AI financial advisor. I can help you with:
                  </p>
                  <ul className="mt-3 space-y-2 text-gray-300">
                    <li className="flex items-center gap-2">
                      <Icons.Target className="w-4 h-4 text-[#C9A227]" />
                      Retirement & financial planning
                    </li>
                    <li className="flex items-center gap-2">
                      <Icons.ChartBar className="w-4 h-4 text-[#C9A227]" />
                      Portfolio analysis & optimization
                    </li>
                    <li className="flex items-center gap-2">
                      <Icons.Lightbulb className="w-4 h-4 text-[#C9A227]" />
                      Investment insights & recommendations
                    </li>
                    <li className="flex items-center gap-2">
                      <Icons.Shield className="w-4 h-4 text-[#C9A227]" />
                      Tax & estate planning guidance
                    </li>
                  </ul>
                </div>
              </div>
            </div>
 
            {/* Quick Prompts */}
            <div className="flex flex-wrap gap-2">
              {quickPrompts.map((prompt, i) => (
                <button
                  key={i}
                  onClick={() => setMessage(prompt)}
                  className="px-3 py-2 rounded-full text-[#C9A227] text-sm hover:bg-[#C9A227]/20 transition-colors"
                  style={{ backgroundColor: 'rgba(201, 162, 39, 0.1)', border: '1px solid rgba(201, 162, 39, 0.2)' }}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
 
          {/* Chat Input */}
          <div className="p-4 border-t border-gray-800/50">
            {userTier === 'Starter' ? (
              <div className="text-center py-4">
                <Icons.Lock className="w-8 h-8 text-gray-500 mx-auto mb-2" />
                <p className="text-gray-400 mb-2">AI Chat requires Growth tier</p>
                <button className="px-4 py-2 rounded-lg bg-gradient-to-r from-[#C9A227] to-[#E8D48B] text-[#0D1B2A] text-sm font-semibold">
                  Upgrade to Growth
                </button>
              </div>
            ) : (
              <div className="flex gap-3">
                <input
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Ask Elson anything about your finances..."
                  className="flex-1 bg-[#0a1520] border border-gray-700 rounded-xl py-3 px-4 text-white placeholder-gray-500 focus:outline-none focus:border-[#C9A227]/50"
                />
                <button className="px-4 py-3 rounded-xl bg-gradient-to-r from-[#C9A227] to-[#E8D48B] text-[#0D1B2A] font-semibold hover:shadow-lg hover:shadow-[#C9A227]/20 transition-all">
                  <Icons.Send className="w-5 h-5" />
                </button>
              </div>
            )}
          </div>
        </Card>
      )}
 
      {activeTab === 'Planning' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { icon: Icons.Target, title: 'Retirement Planning', desc: 'Analyze your retirement readiness', color: 'from-green-500/20 to-green-500/10' },
            { icon: Icons.Learn, title: 'College Planning', desc: '529 plans & education savings', color: 'from-blue-500/20 to-blue-500/10' },
            { icon: Icons.Document, title: 'Estate Planning', desc: 'Will, trusts & beneficiaries', color: 'from-purple-500/20 to-purple-500/10' },
            { icon: Icons.Cash, title: 'Tax Optimization', desc: 'Strategies to reduce tax burden', color: 'from-orange-500/20 to-orange-500/10' },
          ].map((item, i) => (
            <Card key={i} className="p-6 cursor-pointer hover:border-[#C9A227]/40">
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${item.color} flex items-center justify-center mb-4`}>
                <item.icon className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-1">{item.title}</h3>
              <p className="text-sm text-gray-400">{item.desc}</p>
            </Card>
          ))}
        </div>
      )}
 
      {activeTab === 'Insights' && (
        <Card className="p-4">
          <div className="space-y-3">
            {[
              { type: 'buy' as const, symbol: 'NVDA', text: 'Strong momentum with positive sentiment across social and news channels', confidence: 87 },
              { type: 'buy' as const, symbol: 'GOOGL', text: 'Undervalued based on recent earnings beat and AI investments', confidence: 76 },
              { type: 'sell' as const, symbol: 'TSLA', text: 'Sentiment declining 15% this week, consider reducing exposure', confidence: 72 },
              { type: 'alert' as const, text: 'Your tech sector concentration is 45% - consider diversifying', confidence: 95 },
              { type: 'alert' as const, text: 'Cash position at 3% is below recommended 5-10% range', confidence: 88 },
            ].map((insight, i) => (
              <AIInsightRow key={i} insight={insight} />
            ))}
          </div>
        </Card>
      )}
 
      {activeTab === 'Signals' && (
        <Card className="p-4">
          <p className="text-gray-400 text-center py-8">Trading signals based on market analysis</p>
        </Card>
      )}
 
      {activeTab === 'Settings' && (
        <Card className="p-4">
          <p className="text-gray-400 text-center py-8">AI preferences and settings</p>
        </Card>
      )}
    </div>
  );
};
 
// Invest Page
const InvestPage = ({
  userTier,
  holdings
}: {
  userTier: UserTier;
  holdings: Holding[];
}) => {
  const [activeTab, setActiveTab] = useState('Portfolio');
  const tabs = ['Portfolio', 'Positions', 'Orders', 'Auto-Trading', 'Discover'];
 
  return (
    <div className="space-y-4 md:space-y-6" style={{ backgroundColor: '#0D1B2A' }}>
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Invest</h1>
        <p className="text-gray-400 text-sm">Manage your investments and trading</p>
      </div>
 
      <TabGroup tabs={tabs} value={activeTab} onChange={setActiveTab} />
 
      {activeTab === 'Portfolio' && (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
          <Card className="xl:col-span-2">
            <CardHeader title="Holdings" action={() => {}} />
            <div>
              {holdings.map((holding) => (
                <HoldingRow key={holding.symbol} {...holding} />
              ))}
            </div>
          </Card>
 
          <div className="space-y-4">
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-4">Quick Stats</h3>
              <div className="space-y-3">
                {[
                  { label: 'Total Return', value: '+$18,234', color: 'text-green-400' },
                  { label: 'Available Cash', value: '$12,450', color: 'text-white' },
                  { label: 'Active Positions', value: '24', color: 'text-white' },
                  { label: 'Pending Orders', value: '3', color: 'text-white' },
                ].map((stat) => (
                  <div key={stat.label} className="flex items-center justify-between">
                    <span className="text-sm text-gray-400">{stat.label}</span>
                    <span className={`text-sm font-medium ${stat.color}`}>{stat.value}</span>
                  </div>
                ))}
              </div>
            </Card>
 
            <Card className="p-4">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-4">Quick Actions</h3>
              <div className="space-y-2">
                <button className="w-full py-3 rounded-xl bg-gradient-to-r from-[#C9A227] to-[#E8D48B] text-[#0D1B2A] font-semibold">
                  Trade
                </button>
                <button 
                  className="w-full py-3 rounded-xl text-[#C9A227] font-semibold"
                  style={{ backgroundColor: 'rgba(201, 162, 39, 0.15)', border: '1px solid rgba(201, 162, 39, 0.3)' }}
                >
                  Deposit
                </button>
              </div>
            </Card>
          </div>
        </div>
      )}
 
      {activeTab === 'Auto-Trading' && (
        userTier === 'Starter' ? (
          <PremiumLock feature="Auto-Trading" requiredTier="Growth">
            <Card className="p-6">
              <div className="text-center py-8">
                <Icons.AutoTrading className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">Automated Trading Strategies</h3>
                <p className="text-gray-400">Let AI execute trades based on proven strategies</p>
              </div>
            </Card>
          </PremiumLock>
        ) : (
          <Card className="p-4">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-white">Auto-Trading</h3>
                <p className="text-sm text-gray-400">Manage your automated trading strategies</p>
              </div>
              <div className="flex items-center gap-3">
                <span className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                  <span className="text-sm text-green-400">Active</span>
                </span>
                <button 
                  className="px-4 py-2 rounded-lg text-red-400 text-sm font-medium"
                  style={{ backgroundColor: 'rgba(239, 68, 68, 0.2)' }}
                >
                  Pause All
                </button>
              </div>
            </div>
 
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="rounded-xl p-4" style={{ backgroundColor: '#1a2535' }}>
                <p className="text-2xl font-bold text-green-400">+$2,847</p>
                <p className="text-xs text-gray-500">Total P&L</p>
              </div>
              <div className="rounded-xl p-4" style={{ backgroundColor: '#1a2535' }}>
                <p className="text-2xl font-bold text-white">68%</p>
                <p className="text-xs text-gray-500">Win Rate</p>
              </div>
              <div className="rounded-xl p-4" style={{ backgroundColor: '#1a2535' }}>
                <p className="text-2xl font-bold text-white">0.42</p>
                <p className="text-xs text-gray-500">Loss Ratio</p>
              </div>
              <div className="rounded-xl p-4" style={{ backgroundColor: '#1a2535' }}>
                <p className="text-2xl font-bold text-white">47</p>
                <p className="text-xs text-gray-500">Total Trades</p>
              </div>
            </div>
 
            <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Active Strategies</h4>
            <div className="space-y-3">
              {[
                { name: 'RSI Momentum', status: 'Active', pnl: '+$420', trades: 12 },
                { name: 'Mean Reversion', status: 'Active', pnl: '+$180', trades: 8 },
                { name: 'Breakout Strategy', status: 'Active', pnl: '-$52', trades: 5 },
              ].map((strategy) => (
                <div 
                  key={strategy.name} 
                  className="flex items-center justify-between p-4 rounded-xl"
                  style={{ backgroundColor: '#1a2535' }}
                >
                  <div>
                    <p className="text-sm font-medium text-white">{strategy.name}</p>
                    <p className="text-xs text-gray-500">{strategy.trades} trades today</p>
                  </div>
                  <div className="text-right">
                    <p className={`text-sm font-medium ${strategy.pnl.startsWith('+') ? 'text-green-400' : 'text-red-400'}`}>
                      {strategy.pnl}
                    </p>
                    <span className="text-xs text-green-400">{strategy.status}</span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )
      )}
 
      {activeTab === 'Positions' && (
        <Card className="p-4">
          <p className="text-gray-400 text-center py-8">Your current positions</p>
        </Card>
      )}
 
      {activeTab === 'Orders' && (
        <Card className="p-4">
          <p className="text-gray-400 text-center py-8">Order history and pending orders</p>
        </Card>
      )}
 
      {activeTab === 'Discover' && (
        <Card className="p-4">
          <p className="text-gray-400 text-center py-8">Discover new investment opportunities</p>
        </Card>
      )}
    </div>
  );
};
 
// Learn Page
const LearnPage = () => {
  const [activeTab, setActiveTab] = useState('Courses');
  const tabs = ['Courses', 'Tools', 'Progress'];
 
  return (
    <div className="space-y-4 md:space-y-6" style={{ backgroundColor: '#0D1B2A' }}>
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Learn</h1>
        <p className="text-gray-400 text-sm">Build your financial knowledge</p>
      </div>
 
      <TabGroup tabs={tabs} value={activeTab} onChange={setActiveTab} />
 
      {activeTab === 'Courses' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            { level: 'Beginner', title: 'Investing Basics', lessons: 8, duration: '45 min', progress: 60 },
            { level: 'Beginner', title: 'Understanding Risk', lessons: 6, duration: '30 min', progress: 0 },
            { level: 'Intermediate', title: 'Portfolio Diversification', lessons: 10, duration: '1 hr', progress: 25 },
            { level: 'Intermediate', title: 'Tax-Efficient Investing', lessons: 8, duration: '45 min', progress: 0 },
            { level: 'Advanced', title: 'Options Trading', lessons: 12, duration: '2 hr', progress: 0 },
            { level: 'Advanced', title: 'Estate Planning', lessons: 10, duration: '1.5 hr', progress: 0 },
          ].map((course, i) => {
            const levelStyles = {
              Beginner: { backgroundColor: 'rgba(34, 197, 94, 0.2)', color: '#4ADE80' },
              Intermediate: { backgroundColor: 'rgba(59, 130, 246, 0.2)', color: '#60A5FA' },
              Advanced: { backgroundColor: 'rgba(168, 85, 247, 0.2)', color: '#A78BFA' },
            };
            return (
            <Card key={i} className="p-4 cursor-pointer">
              <span 
                className="px-2 py-1 rounded text-xs font-medium"
                style={levelStyles[course.level as keyof typeof levelStyles]}
              >
                {course.level}
              </span>
              <h3 className="text-lg font-semibold text-white mt-3 mb-2">{course.title}</h3>
              <p className="text-sm text-gray-400 mb-4">{course.lessons} lessons · {course.duration}</p>
              {course.progress > 0 && (
                <div className="w-full rounded-full h-2" style={{ backgroundColor: '#374151' }}>
                  <div
                    className="h-2 rounded-full"
                    style={{ width: `${course.progress}%`, background: 'linear-gradient(to right, #C9A227, #E8D48B)' }}
                  />
                </div>
              )}
            </Card>
          )})}
        </div>
      )}
 
      {activeTab === 'Tools' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { icon: Icons.Target, title: 'Retirement Calculator', desc: 'Plan your retirement savings' },
            { icon: Icons.Cash, title: 'Loan Calculator', desc: 'Calculate loan payments' },
            { icon: Icons.Trending, title: 'Investment Growth', desc: 'Project your investment growth' },
            { icon: Icons.Document, title: 'Tax Estimator', desc: 'Estimate your tax burden' },
          ].map((tool, i) => (
            <Card key={i} className="p-6 cursor-pointer hover:border-[#C9A227]/40">
              <div 
                className="w-12 h-12 rounded-xl flex items-center justify-center mb-4"
                style={{ backgroundColor: 'rgba(201, 162, 39, 0.2)' }}
              >
                <tool.icon className="w-6 h-6 text-[#C9A227]" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-1">{tool.title}</h3>
              <p className="text-sm text-gray-400">{tool.desc}</p>
            </Card>
          ))}
        </div>
      )}
 
      {activeTab === 'Progress' && (
        <Card className="p-6">
          <div className="text-center py-8">
            <div 
              className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4"
              style={{ backgroundColor: 'rgba(201, 162, 39, 0.2)' }}
            >
              <span className="text-2xl font-bold text-[#C9A227]">3</span>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Level 3 Investor</h3>
            <p className="text-gray-400 mb-6">You've completed 3 courses and 12 lessons</p>
            <div className="w-full max-w-md mx-auto rounded-full h-3" style={{ backgroundColor: '#374151' }}>
              <div className="h-3 rounded-full" style={{ width: '45%', background: 'linear-gradient(to right, #C9A227, #E8D48B)' }} />
            </div>
            <p className="text-sm text-gray-500 mt-2">450 / 1000 XP to Level 4</p>
          </div>
        </Card>
      )}
    </div>
  );
};
 
// Account Page
const AccountPage = () => {
  const [activeTab, setActiveTab] = useState('Transfers');
  const tabs = ['Transfers', 'Statements', 'Contingency', 'Products'];
 
  return (
    <div className="space-y-4 md:space-y-6" style={{ backgroundColor: '#0D1B2A' }}>
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Account</h1>
        <p className="text-gray-400 text-sm">Manage your account and documents</p>
      </div>
 
      <TabGroup tabs={tabs} value={activeTab} onChange={setActiveTab} />
 
      {activeTab === 'Transfers' && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Transfer Funds</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">From</label>
              <select className="w-full bg-[#0a1520] border border-gray-700 rounded-xl py-3 px-4 text-white appearance-none cursor-pointer focus:outline-none focus:border-[#C9A227]/50" style={{ colorScheme: 'dark' }}>
                <option>Checking Account (****1234)</option>
                <option>Savings Account (****5678)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">To</label>
              <select className="w-full bg-[#0a1520] border border-gray-700 rounded-xl py-3 px-4 text-white appearance-none cursor-pointer focus:outline-none focus:border-[#C9A227]/50" style={{ colorScheme: 'dark' }}>
                <option>Investment Account</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Amount</label>
              <input
                type="text"
                placeholder="$0.00"
                className="w-full bg-[#0a1520] border border-gray-700 rounded-xl py-3 px-4 text-white placeholder-gray-500 focus:outline-none focus:border-[#C9A227]/50"
              />
            </div>
            <button className="w-full py-3 rounded-xl bg-gradient-to-r from-[#C9A227] to-[#E8D48B] text-[#0D1B2A] font-semibold">
              Transfer
            </button>
          </div>
        </Card>
      )}
 
      {activeTab === 'Statements' && (
        <Card className="p-4">
          <div className="space-y-3">
            {[
              { type: 'Monthly Statement', date: 'December 2025', size: '245 KB' },
              { type: 'Monthly Statement', date: 'November 2025', size: '312 KB' },
              { type: 'Tax Document (1099)', date: '2024', size: '128 KB' },
              { type: 'Monthly Statement', date: 'October 2025', size: '287 KB' },
            ].map((doc, i) => (
              <div 
                key={i} 
                className="flex items-center justify-between p-4 rounded-xl"
                style={{ backgroundColor: '#1a2535' }}
              >
                <div className="flex items-center gap-3">
                  <Icons.Document className="w-5 h-5 text-gray-400" />
                  <div>
                    <p className="text-sm font-medium text-white">{doc.type}</p>
                    <p className="text-xs text-gray-500">{doc.date} · {doc.size}</p>
                  </div>
                </div>
                <button className="text-[#C9A227] text-sm font-medium hover:underline">
                  Download
                </button>
              </div>
            ))}
          </div>
        </Card>
      )}
 
      {activeTab === 'Contingency' && (
        <div className="space-y-4">
          {[
            { icon: Icons.Users, title: 'Beneficiaries', desc: '2 primary, 1 contingent', action: 'Manage' },
            { icon: Icons.User, title: 'Trusted Contacts', desc: '1 verified contact', action: 'Manage' },
            { icon: Icons.Document, title: 'Power of Attorney', desc: 'Durable POA active', action: 'View' },
            { icon: Icons.Shield, title: 'Successor Owners', desc: '2 in succession chain', action: 'Manage' },
          ].map((item, i) => (
            <Card key={i} className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div 
                    className="w-12 h-12 rounded-xl flex items-center justify-center"
                    style={{ backgroundColor: 'rgba(201, 162, 39, 0.2)' }}
                  >
                    <item.icon className="w-6 h-6 text-[#C9A227]" />
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-white">{item.title}</h3>
                    <p className="text-sm text-gray-400">{item.desc}</p>
                  </div>
                </div>
                <button 
                  className="px-4 py-2 rounded-lg text-[#C9A227] text-sm font-medium hover:bg-[#C9A227]/20 transition-colors"
                  style={{ backgroundColor: 'rgba(201, 162, 39, 0.1)' }}
                >
                  {item.action}
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}
 
      {activeTab === 'Products' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { icon: Icons.Cash, title: 'Elson Card', desc: 'Premium debit card with rewards', status: 'Active' },
            { icon: Icons.Trending, title: 'High-Yield Savings', desc: '4.5% APY', status: 'Active' },
            { icon: Icons.Shield, title: 'Insurance', desc: 'Life & disability coverage', status: 'Not enrolled' },
          ].map((product, i) => (
            <Card key={i} className="p-6">
              <div className="flex items-center gap-4 mb-4">
                <div 
                  className="w-12 h-12 rounded-xl flex items-center justify-center"
                  style={{ backgroundColor: 'rgba(201, 162, 39, 0.2)' }}
                >
                  <product.icon className="w-6 h-6 text-[#C9A227]" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white">{product.title}</h3>
                  <p className="text-sm text-gray-400">{product.desc}</p>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className={`text-sm ${product.status === 'Active' ? 'text-green-400' : 'text-gray-500'}`}>
                  {product.status}
                </span>
                <button className="text-[#C9A227] text-sm font-medium hover:underline">
                  {product.status === 'Active' ? 'Manage' : 'Learn More'}
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
 
// ============================================
// MAIN APP COMPONENT
// ============================================
export default function ElsonApp() {
  const [tradingMode, setTradingMode] = useState<TradingMode>('Paper');
  const [activePage, setActivePage] = useState<ActivePage>('Dashboard');
  const [userTier] = useState<UserTier>('Growth'); // Change to test different tiers
 
  // Mock data
  const familyMembers: FamilyMember[] = [
    { id: '1', name: 'You', role: 'owner', value: 85000, change: 2.1 },
    { id: '2', name: 'Sarah', role: 'adult', value: 32000, change: 1.5 },
    { id: '3', name: 'Mike', role: 'teen', value: 8845, change: 0.8, pendingApprovals: 1 },
    { id: '4', name: 'Emma', role: 'child', value: 2000, change: 0.5 },
  ];
 
  const portfolio = {
    totalValue: 127845.32,
    dayChange: 2458.90,
    dayChangePercent: 1.96,
  };
 
  const manualTradingStats = {
    today: 1240,
    thisMonth: 4320,
  };
 
  const autoTradingStats = {
    pnl: 2847,
    winRate: 68,
    lossRatio: 0.42,
    trades: 12,
    isActive: true,
  };
 
  const aiInsights: AIInsight[] = [
    { type: 'buy', symbol: 'NVDA', text: 'Strong momentum, positive sentiment', confidence: 87 },
    { type: 'sell', symbol: 'TSLA', text: 'Sentiment declining 15% this week', confidence: 72 },
    { type: 'alert', text: 'Tech concentration: 45% - consider diversifying' },
  ];
 
  const activities = [
    { icon: Icons.ArrowUp, iconColor: 'text-green-400', iconBg: 'rgba(34, 197, 94, 0.2)', title: 'Bought NVDA', subtitle: '5 @ $870.00', time: '2h', isAutoTrade: false },
    { icon: Icons.ArrowDown, iconColor: 'text-red-400', iconBg: 'rgba(239, 68, 68, 0.2)', title: 'Sold AAPL', subtitle: '10 @ $179.50', time: '5h', isAutoTrade: true },
    { icon: Icons.Cash, iconColor: 'text-[#C9A227]', iconBg: 'rgba(201, 162, 39, 0.2)', title: 'Deposit', subtitle: '+$5,000', time: '1d', isAutoTrade: false },
    { icon: Icons.AutoTrading, iconColor: 'text-blue-400', iconBg: 'rgba(59, 130, 246, 0.2)', title: 'Auto Trade', subtitle: 'GOOGL +$45', time: '2d', isAutoTrade: true },
  ];
 
  const holdings = [
    { symbol: 'AAPL', name: 'Apple Inc.', shares: '50 shares', value: '$8,925', change: 2.34, color: 'bg-blue-600' },
    { symbol: 'NVDA', name: 'NVIDIA Corp', shares: '25 shares', value: '$21,882', change: 4.15, color: 'bg-green-600' },
    { symbol: 'MSFT', name: 'Microsoft', shares: '40 shares', value: '$16,624', change: -0.82, color: 'bg-purple-600' },
    { symbol: 'BTC', name: 'Bitcoin', shares: '0.75 BTC', value: '$50,588', change: 1.28, color: 'bg-orange-500' },
  ];
 
  const navItems = [
    { icon: Icons.Dashboard, label: 'Dashboard' as ActivePage },
    { icon: Icons.AI, label: 'Elson AI' as ActivePage },
    { icon: Icons.Invest, label: 'Invest' as ActivePage },
    { icon: Icons.Learn, label: 'Learn' as ActivePage },
    { icon: Icons.Account, label: 'Account' as ActivePage },
  ];
 
  const pendingApprovals = familyMembers.reduce((sum, m) => sum + (m.pendingApprovals || 0), 0);
 
  const renderPage = () => {
    switch (activePage) {
      case 'Dashboard':
        return (
          <DashboardPage
            userTier={userTier}
            tradingMode={tradingMode}
            familyMembers={familyMembers}
            portfolio={portfolio}
            manualTradingStats={manualTradingStats}
            autoTradingStats={autoTradingStats}
            aiInsights={aiInsights}
            activities={activities}
            pendingApprovals={pendingApprovals}
          />
        );
      case 'Elson AI':
        return <ElsonAIPage userTier={userTier} />;
      case 'Invest':
        return <InvestPage userTier={userTier} holdings={holdings} />;
      case 'Learn':
        return <LearnPage />;
      case 'Account':
        return <AccountPage />;
      default:
        return null;
    }
  };
 
  return (
    <div className="min-h-screen text-white" style={{ colorScheme: 'dark', backgroundColor: '#0D1B2A', background: 'linear-gradient(to bottom right, #050A0F, #0D1B2A, #1B2838)' }}>
      {/* Mobile Header */}
      <header className="xl:hidden sticky top-0 z-50" style={{ backgroundColor: '#0D1B2A' }}>
        <MarketStatusStrip />
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#C9A227] to-[#E8D48B] flex items-center justify-center">
              <Icons.Logo className="w-6 h-6 text-[#0D1B2A]" />
            </div>
            <span className="font-serif text-xl font-bold">Elson</span>
          </div>
          <ToggleGroup options={['Paper', 'Live']} value={tradingMode} onChange={(v) => setTradingMode(v as TradingMode)} size="small" />
          <button className="relative p-2 min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-400 hover:text-white">
            <Icons.Bell className="w-6 h-6" />
            <span className="w-2 h-2 rounded-full absolute top-1 right-1" style={{ backgroundColor: '#C9A227' }} />
          </button>
        </div>
        <div className="px-4 pb-3">
          <div className="relative">
            <Icons.Search className="w-5 h-5 absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              type="search"
              placeholder="Search stocks, ETFs, crypto..."
              className="w-full bg-[#0a1520] border border-gray-700 rounded-xl py-3 pl-12 pr-4 text-base text-white placeholder-gray-500 focus:outline-none focus:border-[#C9A227]/50"
            />
          </div>
        </div>
      </header>
 
      <div className="flex min-h-screen" style={{ backgroundColor: '#0D1B2A' }}>
        {/* Desktop Sidebar */}
        <aside className="hidden xl:flex w-64 flex-col sticky top-0 h-screen" style={{ backgroundColor: '#0D1B2A', borderRight: '1px solid rgba(55, 65, 81, 0.5)' }}>
          <div className="p-6" style={{ borderBottom: '1px solid rgba(55, 65, 81, 0.5)' }}>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#C9A227] to-[#E8D48B] flex items-center justify-center">
                <Icons.Logo className="w-6 h-6 text-[#0D1B2A]" />
              </div>
              <div>
                <span className="font-serif text-xl font-bold">Elson</span>
                <p className="text-xs text-gray-500">Financial AI</p>
              </div>
            </div>
          </div>
 
          <div className="p-4">
            <ToggleGroup options={['Paper', 'Live']} value={tradingMode} onChange={(v) => setTradingMode(v as TradingMode)} />
          </div>
 
          <nav className="flex-1 px-3 py-2 overflow-y-auto">
            <div className="space-y-1">
              {navItems.map((item) => (
                <SidebarItem
                  key={item.label}
                  icon={item.icon}
                  label={item.label}
                  active={activePage === item.label}
                  onClick={() => setActivePage(item.label)}
                  badge={item.label === 'Dashboard' ? pendingApprovals : undefined}
                />
              ))}
            </div>
          </nav>
 
          <div className="p-4" style={{ borderTop: '1px solid rgba(55, 65, 81, 0.5)' }}>
            <button className="w-full flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-[#C9A227]/10 transition-all">
              <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: 'linear-gradient(to bottom right, #C9A227, #E8D48B)' }}>
                <span className="text-[#0D1B2A] text-sm font-bold">D</span>
              </div>
              <div className="flex-1 min-w-0 text-left">
                <p className="text-sm font-medium text-white truncate">Desmond</p>
                <div className="flex items-center gap-2">
                  <TierBadge tier={userTier} />
                </div>
              </div>
              <Icons.Settings className="w-5 h-5 text-gray-500" />
            </button>
          </div>
        </aside>
 
        {/* Main Content */}
        <main className="flex-1 overflow-y-auto pb-20 xl:pb-0" style={{ backgroundColor: '#0D1B2A' }}>
          {/* Desktop Top Nav */}
          <header className="hidden xl:block sticky top-0 z-40" style={{ backgroundColor: '#0D1B2A', borderBottom: '1px solid rgba(55, 65, 81, 0.5)' }}>
            <MarketStatusStrip />
            <div className="flex items-center justify-between px-8 py-4 max-w-[1440px] mx-auto">
              <div className="relative w-80">
                <Icons.Search className="w-5 h-5 absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" />
                <input
                  type="search"
                  placeholder="Search stocks, ETFs, crypto..."
                  className="w-full bg-[#0a1520] border border-gray-700 rounded-xl py-3 pl-12 pr-16 text-base text-white placeholder-gray-500 focus:outline-none focus:border-[#C9A227]/50"
                />
                <kbd className="absolute right-4 top-1/2 -translate-y-1/2 text-xs text-gray-500 px-2 py-1 rounded" style={{ backgroundColor: '#1f2937' }}>⌘K</kbd>
              </div>
              <div className="flex items-center gap-4">
                <button className="relative p-3 min-w-[44px] min-h-[44px] text-gray-400 hover:text-white transition-colors rounded-lg">
                  <Icons.Bell className="w-5 h-5" />
                  <span className="w-2 h-2 rounded-full absolute top-2 right-2" style={{ backgroundColor: '#C9A227' }} />
                </button>
                <button className="p-3 min-w-[44px] min-h-[44px] text-gray-400 hover:text-white transition-colors rounded-lg">
                  <Icons.Help className="w-5 h-5" />
                </button>
              </div>
            </div>
          </header>
 
          {/* Page Content */}
          <div className="p-4 md:p-6 xl:p-8 max-w-[1440px] mx-auto" style={{ backgroundColor: '#0D1B2A', minHeight: '100%' }}>
            {renderPage()}
          </div>
        </main>
      </div>
 
      {/* Mobile Bottom Navigation */}
      <nav className="xl:hidden fixed bottom-0 left-0 right-0 pb-[env(safe-area-inset-bottom)]" style={{ backgroundColor: '#050A0F', borderTop: '1px solid rgba(201, 162, 39, 0.1)' }}>
        <div className="flex items-center justify-around max-w-md mx-auto py-2">
          {navItems.map((item) => (
            <BottomNavItem
              key={item.label}
              icon={item.icon}
              label={item.label === 'Elson AI' ? 'AI' : item.label}
              active={activePage === item.label}
              onClick={() => setActivePage(item.label)}
            />
          ))}
        </div>
      </nav>
    </div>
  );
}
