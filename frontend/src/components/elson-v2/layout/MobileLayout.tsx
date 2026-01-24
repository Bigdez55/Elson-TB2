import React, { useState } from 'react';
import { C } from '../primitives/Colors';
import { MobileHeader } from './MobileHeader';
import { MobileBottomNav } from './MobileBottomNav';
import { useMarketTimer } from '../hooks/useMarketTimer';
import type { TabId, TradingMode } from '../types';

// Import tabs - these will be created next
import { Dashboard } from '../tabs/Dashboard/Dashboard';
import { AITab } from '../tabs/AITab/AITab';
import { InvestTab } from '../tabs/InvestTab/InvestTab';
import { WealthTab } from '../tabs/WealthTab/WealthTab';
import { AccountTab } from '../tabs/AccountTab/AccountTab';

interface MobileLayoutProps {
  initialTab?: TabId;
  initialMode?: TradingMode;
}

export const MobileLayout = ({
  initialTab = 'dashboard',
  initialMode = 'paper',
}: MobileLayoutProps) => {
  const [tab, setTab] = useState<TabId>(initialTab);
  const [mode, setMode] = useState<TradingMode>(initialMode);
  const [searchQuery, setSearchQuery] = useState('');
  const { isOpen, timeStr } = useMarketTimer();

  const renderTab = () => {
    switch (tab) {
      case 'dashboard':
        return <Dashboard nav={setTab} />;
      case 'ai':
        return <AITab />;
      case 'invest':
        return <InvestTab />;
      case 'wealth':
        return <WealthTab />;
      case 'account':
        return <AccountTab />;
      default:
        return <Dashboard nav={setTab} />;
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        backgroundColor: C.bg,
        fontFamily: 'system-ui, -apple-system, sans-serif',
      }}
    >
      <MobileHeader
        isMarketOpen={isOpen}
        marketTimeStr={timeStr}
        mode={mode}
        onModeChange={setMode}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
      />

      <main
        style={{
          maxWidth: 480,
          margin: '0 auto',
          padding: '20px 16px 100px',
        }}
      >
        {renderTab()}
      </main>

      <MobileBottomNav activeTab={tab} onTabChange={setTab} />
    </div>
  );
};
