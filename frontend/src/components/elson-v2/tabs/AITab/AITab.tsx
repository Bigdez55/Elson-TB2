import React, { useState } from 'react';
import { C } from '../../primitives/Colors';
import { Icons } from '../../primitives/Icons';
import { Card, Inner } from '../../ui/Card';
import { Badge } from '../../ui/Badge';
import { SubTab } from '../../ui/Button';
import { Toggle } from '../../ui/Toggle';
import { Txt } from '../../ui/Text';
import { user } from '../../data/mockData';
import type { Message } from '../../types';

type AISubTab = 'chat' | 'insights' | 'advisor' | 'trading';

export const AITab = () => {
  const [sub, setSub] = useState<AISubTab>('chat');
  const [msgs, setMsgs] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: `Hello ${user.name}! I'm your AI wealth advisor. How can I help optimize your portfolio today?`,
    },
  ]);
  const [input, setInput] = useState('');
  const [botEnabled, setBotEnabled] = useState(true);
  const [botStrategy, setBotStrategy] = useState<'conservative' | 'balanced' | 'aggressive'>('balanced');

  const suggestions = [
    'Analyze my portfolio risk',
    'What should I buy today?',
    'Tax optimization tips',
    'Rebalancing suggestions',
  ];

  const send = () => {
    if (!input.trim()) return;
    setMsgs((p) => [...p, { id: Date.now().toString(), role: 'user', content: input }]);
    const q = input;
    setInput('');
    setTimeout(
      () =>
        setMsgs((p) => [
          ...p,
          {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: `Based on your ${user.risk.toLowerCase()} risk profile and current market conditions, I recommend: ${q.includes('sell') ? 'holding your current positions' : 'diversifying into defensive sectors'}. Would you like me to analyze specific opportunities?`,
          },
        ]),
      800
    );
  };

  const insights = [
    {
      title: 'Portfolio Rebalancing Alert',
      desc: 'Your tech allocation has grown to 45%. Consider rebalancing.',
      type: 'warning' as const,
      action: 'Review',
    },
    {
      title: 'Dividend Opportunity',
      desc: 'XOM offers 3.2% yield with strong fundamentals.',
      type: 'success' as const,
      action: 'Analyze',
    },
    {
      title: 'Risk Alert',
      desc: 'Market volatility increased 15% this week.',
      type: 'danger' as const,
      action: 'Details',
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Navigation */}
      <Card style={{ display: 'flex', justifyContent: 'center', gap: 8, padding: 8 }}>
        <SubTab active={sub === 'chat'} onClick={() => setSub('chat')}>
          Chat
        </SubTab>
        <SubTab active={sub === 'insights'} onClick={() => setSub('insights')}>
          Insights
        </SubTab>
        <SubTab active={sub === 'advisor'} onClick={() => setSub('advisor')}>
          Advisor
        </SubTab>
        <SubTab active={sub === 'trading'} onClick={() => setSub('trading')}>
          Bot
        </SubTab>
      </Card>

      {/* Chat Tab */}
      {sub === 'chat' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* AI Status */}
          <Card style={{ display: 'flex', alignItems: 'center', gap: 14, padding: 14, border: `1px solid ${C.gold}33` }}>
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
                <Icons.Brain />
              </span>
            </div>
            <div style={{ flex: 1 }}>
              <Txt bold style={{ color: C.white }}>
                Elson AI Advisor
              </Txt>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
                <div style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: C.green }} />
                <Txt c="gray" size={12}>
                  Online · {user.risk} risk profile
                </Txt>
              </div>
            </div>
          </Card>

          {/* Messages */}
          <Card style={{ maxHeight: 300, overflowY: 'auto' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {msgs.map((m) => (
                <div
                  key={m.id}
                  style={{
                    display: 'flex',
                    justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start',
                  }}
                >
                  <div
                    style={{
                      maxWidth: '80%',
                      padding: '10px 14px',
                      borderRadius: 16,
                      backgroundColor: m.role === 'user' ? C.gold : C.inner,
                      color: m.role === 'user' ? C.bg : C.white,
                    }}
                  >
                    <Txt size={14} style={{ color: 'inherit' }}>
                      {m.content}
                    </Txt>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Suggestions */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {suggestions.map((s) => (
              <button
                key={s}
                onClick={() => setInput(s)}
                style={{
                  padding: '8px 12px',
                  borderRadius: 20,
                  backgroundColor: C.inner,
                  border: `1px solid ${C.border}`,
                  color: C.gray,
                  fontSize: 12,
                  cursor: 'pointer',
                }}
              >
                {s}
              </button>
            ))}
          </div>

          {/* Input */}
          <Card style={{ padding: 10 }}>
            <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && send()}
                placeholder="Ask anything about your portfolio..."
                style={{
                  flex: 1,
                  backgroundColor: C.inner,
                  border: 'none',
                  borderRadius: 10,
                  padding: '12px 16px',
                  color: C.white,
                  fontSize: 14,
                  outline: 'none',
                }}
              />
              <button
                onClick={send}
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: 22,
                  backgroundColor: C.gold,
                  border: 'none',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: C.bg,
                }}
              >
                <Icons.Send />
              </button>
            </div>
          </Card>
        </div>
      )}

      {/* Insights Tab */}
      {sub === 'insights' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {insights.map((insight, i) => (
            <Card key={i}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <Txt bold>{insight.title}</Txt>
                    <Badge v={insight.type}>{insight.type}</Badge>
                  </div>
                  <Txt c="gray" size={13}>
                    {insight.desc}
                  </Txt>
                </div>
                <button
                  style={{
                    padding: '8px 16px',
                    borderRadius: 8,
                    backgroundColor: C.gold,
                    color: C.bg,
                    border: 'none',
                    fontWeight: 600,
                    fontSize: 12,
                    cursor: 'pointer',
                  }}
                >
                  {insight.action}
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Advisor Tab */}
      {sub === 'advisor' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card>
            <Txt bold size={16} style={{ marginBottom: 12 }}>
              Investment Recommendations
            </Txt>
            <Inner>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <Txt>Diversification Score</Txt>
                <Txt c="gold" bold>
                  72/100
                </Txt>
              </div>
              <Txt c="gray" size={12}>
                Consider adding bonds or international exposure to improve diversification.
              </Txt>
            </Inner>
          </Card>

          <Card>
            <Txt bold size={16} style={{ marginBottom: 12 }}>
              Suggested Actions
            </Txt>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {['Rebalance to target allocation', 'Consider tax-loss harvesting', 'Review dividend reinvestment'].map(
                (action, i) => (
                  <Inner key={i}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Txt size={14}>{action}</Txt>
                      <span style={{ color: C.gold }}>
                        <Icons.ChevronRight />
                      </span>
                    </div>
                  </Inner>
                )
              )}
            </div>
          </Card>
        </div>
      )}

      {/* Trading Bot Tab */}
      {sub === 'trading' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card style={{ border: `1px solid ${C.gold}33` }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
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
                <div>
                  <Txt bold>AI Trading Bot</Txt>
                  <Txt c={botEnabled ? 'green' : 'gray'} size={12}>
                    {botEnabled ? 'Active' : 'Paused'}
                  </Txt>
                </div>
              </div>
              <Toggle on={botEnabled} onToggle={() => setBotEnabled(!botEnabled)} />
            </div>

            <Inner>
              <Txt c="gray" size={12} style={{ marginBottom: 8 }}>
                Strategy
              </Txt>
              <div style={{ display: 'flex', gap: 8 }}>
                {(['conservative', 'balanced', 'aggressive'] as const).map((s) => (
                  <SubTab key={s} active={botStrategy === s} onClick={() => setBotStrategy(s)}>
                    {s.charAt(0).toUpperCase() + s.slice(1)}
                  </SubTab>
                ))}
              </div>
            </Inner>
          </Card>

          <Card>
            <Txt bold size={16} style={{ marginBottom: 12 }}>
              Bot Performance
            </Txt>
            <div style={{ display: 'flex', gap: 12 }}>
              <Inner style={{ flex: 1, textAlign: 'center' }}>
                <Txt c="gray" size={11}>
                  Today
                </Txt>
                <Txt c="green" bold size={18}>
                  +$847
                </Txt>
              </Inner>
              <Inner style={{ flex: 1, textAlign: 'center' }}>
                <Txt c="gray" size={11}>
                  This Week
                </Txt>
                <Txt c="green" bold size={18}>
                  +$2,140
                </Txt>
              </Inner>
              <Inner style={{ flex: 1, textAlign: 'center' }}>
                <Txt c="gray" size={11}>
                  Total
                </Txt>
                <Txt c="green" bold size={18}>
                  +$12,580
                </Txt>
              </Inner>
            </div>
          </Card>

          <Card>
            <Txt bold size={16} style={{ marginBottom: 12 }}>
              Recent Trades
            </Txt>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                { symbol: 'AAPL', action: 'Buy', amount: '$500', time: '2m ago', profit: '+$12.50' },
                { symbol: 'NVDA', action: 'Sell', amount: '$800', time: '15m ago', profit: '+$45.20' },
                { symbol: 'MSFT', action: 'Buy', amount: '$600', time: '1h ago', profit: '+$8.30' },
              ].map((trade, i) => (
                <Inner key={i}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Txt bold>{trade.symbol}</Txt>
                        <Badge v={trade.action === 'Buy' ? 'success' : 'danger'}>{trade.action}</Badge>
                      </div>
                      <Txt c="gray" size={12}>
                        {trade.amount} · {trade.time}
                      </Txt>
                    </div>
                    <Txt c="green" bold>
                      {trade.profit}
                    </Txt>
                  </div>
                </Inner>
              ))}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
