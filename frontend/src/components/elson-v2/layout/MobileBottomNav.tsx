import React from 'react';
import { C } from '../primitives/Colors';
import { Icons } from '../primitives/Icons';
import type { TabId } from '../types';

interface TabConfig {
  id: TabId;
  label: string;
  icon: React.ReactNode;
}

const tabs: TabConfig[] = [
  { id: 'dashboard', label: 'Dashboard', icon: <Icons.Home /> },
  { id: 'ai', label: 'AI', icon: <Icons.Brain /> },
  { id: 'invest', label: 'Invest', icon: <Icons.TrendingUp /> },
  { id: 'wealth', label: 'Wealth', icon: <Icons.Wallet /> },
  { id: 'account', label: 'Account', icon: <Icons.User /> },
];

interface MobileBottomNavProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
}

export const MobileBottomNav = ({ activeTab, onTabChange }: MobileBottomNavProps) => {
  return (
    <nav
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        padding: '8px 16px 24px',
        backgroundColor: C.card,
        borderTop: `1px solid ${C.border}`,
        zIndex: 100,
      }}
    >
      <div
        style={{
          maxWidth: 480,
          margin: '0 auto',
          display: 'flex',
          justifyContent: 'space-around',
        }}
      >
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => onTabChange(t.id)}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 4,
              padding: 8,
              color: activeTab === t.id ? C.gold : C.gray,
              transition: 'color 0.2s',
            }}
          >
            {t.icon}
            <span style={{ fontSize: 11, fontWeight: 600 }}>{t.label}</span>
          </button>
        ))}
      </div>
    </nav>
  );
};
