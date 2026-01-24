import React, { useState } from 'react';
import { C } from '../../primitives/Colors';
import { Icons } from '../../primitives/Icons';
import { Card, Inner } from '../../ui/Card';
import { Badge } from '../../ui/Badge';
import { SubTab, GoldBtn } from '../../ui/Button';
import { Txt } from '../../ui/Text';
import { PortfolioChart } from '../../charts/PortfolioChart';
import { CandlestickChart } from '../../charts/CandlestickChart';
import { holdings, stocks, crypto } from '../../data/mockData';

type InvestSubTab = 'portfolio' | 'trade' | 'discover' | 'crypto';

export const InvestTab = () => {
  const [sub, setSub] = useState<InvestSubTab>('portfolio');
  const [selectedStock, setSelectedStock] = useState(stocks[0]);
  const [order, setOrder] = useState<'buy' | 'sell'>('buy');
  const [shares, setShares] = useState('10');
  const [timeRange, setTimeRange] = useState('1Y');

  const total = holdings.reduce((s, h) => s + h.value, 0);
  const gain = holdings.reduce((s, h) => s + h.gain, 0);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Navigation */}
      <Card style={{ display: 'flex', justifyContent: 'center', gap: 8, padding: 8 }}>
        <SubTab active={sub === 'portfolio'} onClick={() => setSub('portfolio')}>
          Portfolio
        </SubTab>
        <SubTab active={sub === 'trade'} onClick={() => setSub('trade')}>
          Trade
        </SubTab>
        <SubTab active={sub === 'discover'} onClick={() => setSub('discover')}>
          Discover
        </SubTab>
        <SubTab active={sub === 'crypto'} onClick={() => setSub('crypto')}>
          Crypto
        </SubTab>
      </Card>

      {/* Portfolio Tab */}
      {sub === 'portfolio' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Portfolio Summary */}
          <Card>
            <Txt c="gray" size={13}>
              Total Value
            </Txt>
            <Txt bold size={28} style={{ marginTop: 4 }}>
              ${total.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </Txt>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
              <span style={{ color: C.green }}>
                <Icons.TrendingUp />
              </span>
              <Txt c="green" size={14}>
                +${gain.toLocaleString()} (+{((gain / (total - gain)) * 100).toFixed(2)}%)
              </Txt>
            </div>

            <PortfolioChart timeRange={timeRange} endValue={total} />

            <div style={{ display: 'flex', justifyContent: 'center', gap: 6, marginTop: 12 }}>
              {['1D', '1W', '1M', '1Y', 'ALL'].map((t) => (
                <SubTab key={t} active={timeRange === t} onClick={() => setTimeRange(t)}>
                  {t}
                </SubTab>
              ))}
            </div>
          </Card>

          {/* Holdings List */}
          <Card>
            <Txt bold size={16} style={{ marginBottom: 12 }}>
              Holdings
            </Txt>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {holdings.map((h) => (
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
                          fontSize: 11,
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
                          {h.shares} @ ${h.avgCost}
                        </Txt>
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <Txt bold size={14}>
                        ${h.value.toLocaleString()}
                      </Txt>
                      <Txt c={h.gain >= 0 ? 'green' : 'red'} size={12}>
                        {h.gain >= 0 ? '+' : ''}${h.gain.toLocaleString()} ({h.gainPercent.toFixed(1)}%)
                      </Txt>
                    </div>
                  </div>
                </Inner>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Trade Tab */}
      {sub === 'trade' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Stock Selector */}
          <Card>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <div>
                <Txt bold size={20}>
                  {selectedStock.symbol}
                </Txt>
                <Txt c="gray" size={12}>
                  {selectedStock.name}
                </Txt>
              </div>
              <div style={{ textAlign: 'right' }}>
                <Txt bold size={20}>
                  ${selectedStock.price.toFixed(2)}
                </Txt>
                <Txt c={selectedStock.pct >= 0 ? 'green' : 'red'} size={12}>
                  {selectedStock.pct >= 0 ? '+' : ''}
                  {selectedStock.pct.toFixed(2)}%
                </Txt>
              </div>
            </div>

            <CandlestickChart symbol={selectedStock.symbol} isUp={selectedStock.pct >= 0} />
          </Card>

          {/* Order Form */}
          <Card>
            <div style={{ display: 'flex', marginBottom: 16 }}>
              <button
                onClick={() => setOrder('buy')}
                style={{
                  flex: 1,
                  padding: '12px',
                  border: 'none',
                  borderRadius: '10px 0 0 10px',
                  backgroundColor: order === 'buy' ? C.green : C.inner,
                  color: order === 'buy' ? C.white : C.gray,
                  fontWeight: 700,
                  cursor: 'pointer',
                }}
              >
                Buy
              </button>
              <button
                onClick={() => setOrder('sell')}
                style={{
                  flex: 1,
                  padding: '12px',
                  border: 'none',
                  borderRadius: '0 10px 10px 0',
                  backgroundColor: order === 'sell' ? C.red : C.inner,
                  color: order === 'sell' ? C.white : C.gray,
                  fontWeight: 700,
                  cursor: 'pointer',
                }}
              >
                Sell
              </button>
            </div>

            <div style={{ marginBottom: 16 }}>
              <Txt c="gray" size={12}>
                Number of Shares
              </Txt>
              <input
                type="number"
                value={shares}
                onChange={(e) => setShares(e.target.value)}
                style={{
                  width: '100%',
                  backgroundColor: C.inner,
                  border: `1px solid ${C.border}`,
                  borderRadius: 10,
                  padding: '12px 16px',
                  color: C.white,
                  fontSize: 16,
                  marginTop: 6,
                  outline: 'none',
                }}
              />
            </div>

            <Inner style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <Txt c="gray">Market Price</Txt>
                <Txt bold>${selectedStock.price.toFixed(2)}</Txt>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Txt c="gray">Estimated Total</Txt>
                <Txt bold c="gold">
                  ${(selectedStock.price * Number(shares)).toFixed(2)}
                </Txt>
              </div>
            </Inner>

            <GoldBtn full>
              {order === 'buy' ? 'Buy' : 'Sell'} {shares} shares
            </GoldBtn>
          </Card>

          {/* Stock List */}
          <Card>
            <Txt bold size={16} style={{ marginBottom: 12 }}>
              Popular Stocks
            </Txt>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {stocks.slice(0, 5).map((s) => (
                <Inner
                  key={s.symbol}
                  style={{ cursor: 'pointer' }}
                  onClick={() => setSelectedStock(s)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <Txt bold>{s.symbol}</Txt>
                      <Txt c="gray" size={12}>
                        {s.name}
                      </Txt>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <Txt bold>${s.price.toFixed(2)}</Txt>
                      <Txt c={s.pct >= 0 ? 'green' : 'red'} size={12}>
                        {s.pct >= 0 ? '+' : ''}
                        {s.pct.toFixed(2)}%
                      </Txt>
                    </div>
                  </div>
                </Inner>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Discover Tab */}
      {sub === 'discover' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card>
            <Txt bold size={16} style={{ marginBottom: 12 }}>
              Top Movers
            </Txt>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {stocks
                .sort((a, b) => Math.abs(b.pct) - Math.abs(a.pct))
                .slice(0, 4)
                .map((s) => (
                  <Inner key={s.symbol}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <Txt bold>{s.symbol}</Txt>
                        <Txt c="gray" size={12}>
                          {s.name}
                        </Txt>
                      </div>
                      <Badge v={s.pct >= 0 ? 'success' : 'danger'}>
                        {s.pct >= 0 ? '+' : ''}
                        {s.pct.toFixed(2)}%
                      </Badge>
                    </div>
                  </Inner>
                ))}
            </div>
          </Card>

          <Card>
            <Txt bold size={16} style={{ marginBottom: 12 }}>
              Sectors
            </Txt>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {['Technology', 'Healthcare', 'Finance', 'Energy', 'Consumer', 'Industrial'].map((sector) => (
                <button
                  key={sector}
                  style={{
                    padding: '10px 16px',
                    borderRadius: 20,
                    backgroundColor: C.inner,
                    border: `1px solid ${C.border}`,
                    color: C.white,
                    fontSize: 13,
                    cursor: 'pointer',
                  }}
                >
                  {sector}
                </button>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Crypto Tab */}
      {sub === 'crypto' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card>
            <Txt bold size={16} style={{ marginBottom: 12 }}>
              Your Crypto
            </Txt>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {crypto.map((c) => (
                <Inner key={c.symbol}>
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
                          color: c.symbol === 'BTC' ? '#F7931A' : c.symbol === 'ETH' ? '#627EEA' : C.purple,
                        }}
                      >
                        {c.symbol}
                      </div>
                      <div>
                        <Txt bold size={14}>
                          {c.name}
                        </Txt>
                        <Txt c="gray" size={12}>
                          {c.hold} {c.symbol}
                        </Txt>
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <Txt bold size={14}>
                        ${(c.price * c.hold).toLocaleString()}
                      </Txt>
                      <Txt c={c.change >= 0 ? 'green' : 'red'} size={12}>
                        {c.change >= 0 ? '+' : ''}
                        {c.change.toFixed(2)}%
                      </Txt>
                    </div>
                  </div>
                </Inner>
              ))}
            </div>
          </Card>

          <div style={{ display: 'flex', gap: 12 }}>
            <GoldBtn full>Buy Crypto</GoldBtn>
            <GoldBtn full outline>
              Sell Crypto
            </GoldBtn>
          </div>
        </div>
      )}
    </div>
  );
};
