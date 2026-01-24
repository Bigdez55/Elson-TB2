import React, { useState } from 'react';
import { C } from '../../primitives/Colors';
import { Icons } from '../../primitives/Icons';
import { Card, Inner } from '../../ui/Card';
import { Badge } from '../../ui/Badge';
import { SubTab } from '../../ui/Button';
import { Txt } from '../../ui/Text';
import { PortfolioChart } from '../../charts/PortfolioChart';
import { holdings, user } from '../../data/mockData';
import type { TabId } from '../../types';

interface DashboardProps {
  nav: (tab: TabId) => void;
}

export const Dashboard = ({ nav }: DashboardProps) => {
  const [timeRange, setTimeRange] = useState('1W');
  const total = holdings.reduce((s, h) => s + h.value, 0);
  const gain = holdings.reduce((s, h) => s + h.gain, 0);
  const gainPct = ((gain / (total - gain)) * 100).toFixed(2);

  const timeRanges = ['1D', '1W', '1M', '3M', '1Y', 'ALL'];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Portfolio Value Card */}
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <Txt c="gray" size={13}>
              Total Portfolio Value
            </Txt>
            <div style={{ marginTop: 6 }}>
              <Txt c="white" size={32} bold>
                ${total.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </Txt>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 6 }}>
              <span style={{ color: C.green }}>
                <Icons.TrendingUp />
              </span>
              <Txt c="green" size={14} bold>
                +${gain.toLocaleString('en-US', { minimumFractionDigits: 2 })} (+{gainPct}%)
              </Txt>
            </div>
          </div>
          <Badge v="gold">{user.tier}</Badge>
        </div>

        {/* Chart */}
        <PortfolioChart timeRange={timeRange} endValue={total} />

        {/* Time Range Selector */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: 6, marginTop: 12 }}>
          {timeRanges.map((t) => (
            <SubTab key={t} active={timeRange === t} onClick={() => setTimeRange(t)}>
              {t}
            </SubTab>
          ))}
        </div>
      </Card>

      {/* Quick Actions */}
      <div style={{ display: 'flex', gap: 12 }}>
        <Card style={{ flex: 1, textAlign: 'center', cursor: 'pointer' }} onClick={() => nav('invest')}>
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: 22,
              background: `linear-gradient(135deg, ${C.gold}33, ${C.gold}11)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 10px',
            }}
          >
            <span style={{ color: C.gold }}>
              <Icons.TrendingUp />
            </span>
          </div>
          <Txt bold size={13}>
            Trade
          </Txt>
        </Card>
        <Card style={{ flex: 1, textAlign: 'center', cursor: 'pointer' }} onClick={() => nav('wealth')}>
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: 22,
              background: `linear-gradient(135deg, ${C.green}33, ${C.green}11)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 10px',
            }}
          >
            <span style={{ color: C.green }}>
              <Icons.DollarSign />
            </span>
          </div>
          <Txt bold size={13}>
            Deposit
          </Txt>
        </Card>
        <Card style={{ flex: 1, textAlign: 'center', cursor: 'pointer' }} onClick={() => nav('ai')}>
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: 22,
              background: `linear-gradient(135deg, ${C.purple}33, ${C.purple}11)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 10px',
            }}
          >
            <span style={{ color: C.purple }}>
              <Icons.Brain />
            </span>
          </div>
          <Txt bold size={13}>
            AI
          </Txt>
        </Card>
      </div>

      {/* AI Trading Bot Card */}
      <Card style={{ border: `1px solid ${C.gold}33` }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
          <div
            style={{
              width: 48,
              height: 48,
              borderRadius: 24,
              background: `linear-gradient(135deg, ${C.gold}, ${C.goldLight})`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <span style={{ color: C.bg }}>
              <Icons.Bot />
            </span>
          </div>
          <div style={{ flex: 1 }}>
            <Txt bold>AI Trading Bot</Txt>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 2 }}>
              <div
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: 4,
                  backgroundColor: C.green,
                }}
              />
              <Txt c="green" size={12}>
                Active
              </Txt>
            </div>
          </div>
          <Badge v="success">+$847.32 today</Badge>
        </div>

        <Inner>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <Txt c="gray" size={12}>
              Today's Performance
            </Txt>
            <Txt c="green" size={12} bold>
              +2.01%
            </Txt>
          </div>
          <div style={{ display: 'flex', gap: 16 }}>
            <div style={{ flex: 1 }}>
              <Txt c="gray" size={11}>
                Trades
              </Txt>
              <Txt bold size={16}>
                12
              </Txt>
            </div>
            <div style={{ flex: 1 }}>
              <Txt c="gray" size={11}>
                Win Rate
              </Txt>
              <Txt bold size={16}>
                75%
              </Txt>
            </div>
            <div style={{ flex: 1 }}>
              <Txt c="gray" size={11}>
                Profit
              </Txt>
              <Txt c="green" bold size={16}>
                +$847
              </Txt>
            </div>
          </div>
        </Inner>
      </Card>

      {/* Holdings */}
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <Txt bold size={16}>
            Your Holdings
          </Txt>
          <button
            onClick={() => nav('invest')}
            style={{
              background: 'none',
              border: 'none',
              color: C.gold,
              cursor: 'pointer',
              fontSize: 13,
              fontWeight: 600,
            }}
          >
            View All →
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {holdings.slice(0, 4).map((h) => (
            <Inner key={h.symbol}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div
                    style={{
                      width: 40,
                      height: 40,
                      borderRadius: 20,
                      backgroundColor: C.card,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 700,
                      fontSize: 12,
                      color: C.gold,
                    }}
                  >
                    {h.symbol.slice(0, 2)}
                  </div>
                  <div>
                    <Txt bold size={14}>
                      {h.symbol}
                    </Txt>
                    <Txt c="gray" size={12}>
                      {h.shares} shares
                    </Txt>
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <Txt bold size={14}>
                    ${h.value.toLocaleString()}
                  </Txt>
                  <Txt c={h.gain >= 0 ? 'green' : 'red'} size={12}>
                    {h.gain >= 0 ? '+' : ''}
                    {h.gainPercent.toFixed(2)}%
                  </Txt>
                </div>
              </div>
            </Inner>
          ))}
        </div>
      </Card>

      {/* Watchlist */}
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <Txt bold size={16}>
            Watchlist
          </Txt>
          <span style={{ color: C.gold }}>
            <Icons.Plus />
          </span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {['AMZN', 'META', 'AMD'].map((symbol) => {
            const stock = holdings.find((h) => h.symbol === symbol) || {
              symbol,
              currentPrice: Math.random() * 500 + 100,
              gainPercent: (Math.random() - 0.5) * 10,
            };
            return (
              <div
                key={symbol}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '8px 0',
                  borderBottom: `1px solid ${C.border}`,
                }}
              >
                <Txt bold>{symbol}</Txt>
                <div style={{ textAlign: 'right' }}>
                  <Txt bold>${stock.currentPrice?.toFixed(2)}</Txt>
                  <Txt c={stock.gainPercent >= 0 ? 'green' : 'red'} size={12}>
                    {stock.gainPercent >= 0 ? '+' : ''}
                    {stock.gainPercent?.toFixed(2)}%
                  </Txt>
                </div>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
};
