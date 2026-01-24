import React from 'react';
import { C } from '../primitives/Colors';
import { Icons } from '../primitives/Icons';
import { Logo } from '../primitives/Logo';
import { Txt } from '../ui/Text';
import type { TradingMode } from '../types';

interface MobileHeaderProps {
  isMarketOpen: boolean;
  marketTimeStr: string;
  mode: TradingMode;
  onModeChange: (mode: TradingMode) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
}

export const MobileHeader = ({
  isMarketOpen,
  marketTimeStr,
  mode,
  onModeChange,
  searchQuery,
  onSearchChange,
}: MobileHeaderProps) => {
  return (
    <header
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 50,
        padding: '12px 16px',
        backgroundColor: C.bg,
        borderBottom: `1px solid ${C.border}`,
      }}
    >
      <div
        style={{
          maxWidth: 480,
          margin: '0 auto',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Logo />
          <span
            style={{
              fontSize: 20,
              fontWeight: 700,
              color: C.white,
              fontFamily: 'Georgia, serif',
            }}
          >
            Elson
          </span>
        </div>

        {/* Market Status */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '6px 12px',
            backgroundColor: C.inner,
            borderRadius: 20,
          }}
        >
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: 4,
              backgroundColor: isMarketOpen ? C.green : C.red,
              boxShadow: isMarketOpen ? `0 0 8px ${C.green}` : 'none',
            }}
          />
          <Txt c="grayLight" size={12}>
            {isMarketOpen ? `Open · ${marketTimeStr}` : 'Closed'}
          </Txt>
        </div>

        {/* Notification Bell */}
        <button
          style={{
            background: 'none',
            border: 'none',
            color: C.gray,
            cursor: 'pointer',
            position: 'relative',
            padding: 8,
          }}
        >
          <Icons.Bell />
          <div
            style={{
              position: 'absolute',
              top: 6,
              right: 6,
              width: 10,
              height: 10,
              borderRadius: 5,
              backgroundColor: C.gold,
              border: `2px solid ${C.bg}`,
            }}
          />
        </button>
      </div>

      {/* Paper/Live Toggle + Search */}
      <div
        style={{
          maxWidth: 480,
          margin: '12px auto 0',
          display: 'flex',
          gap: 12,
          alignItems: 'center',
        }}
      >
        {/* Paper/Live Toggle */}
        <div
          style={{
            display: 'flex',
            backgroundColor: C.inner,
            borderRadius: 10,
            padding: 4,
          }}
        >
          <button
            onClick={() => onModeChange('paper')}
            style={{
              padding: '8px 18px',
              borderRadius: 8,
              border: 'none',
              cursor: 'pointer',
              backgroundColor: mode === 'paper' ? C.gold : 'transparent',
              color: mode === 'paper' ? C.bg : C.gray,
              fontWeight: 700,
              fontSize: 13,
            }}
          >
            Paper
          </button>
          <button
            onClick={() => onModeChange('live')}
            style={{
              padding: '8px 18px',
              borderRadius: 8,
              border: 'none',
              cursor: 'pointer',
              backgroundColor: mode === 'live' ? C.gold : 'transparent',
              color: mode === 'live' ? C.bg : C.gray,
              fontWeight: 700,
              fontSize: 13,
            }}
          >
            Live
          </button>
        </div>

        {/* Search */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            backgroundColor: C.inner,
            borderRadius: 10,
            padding: '10px 14px',
          }}
        >
          <span style={{ color: C.gray }}>
            <Icons.Search />
          </span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search stocks, crypto..."
            style={{
              flex: 1,
              background: 'none',
              border: 'none',
              outline: 'none',
              color: C.white,
              fontSize: 14,
            }}
          />
        </div>
      </div>
    </header>
  );
};
