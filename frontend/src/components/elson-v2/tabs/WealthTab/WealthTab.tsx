import React, { useState } from 'react';
import { C } from '../../primitives/Colors';
import { Icons } from '../../primitives/Icons';
import { Card, Inner } from '../../ui/Card';
import { Badge } from '../../ui/Badge';
import { SubTab, GoldBtn } from '../../ui/Button';
import { Input } from '../../ui/Input';
import { Txt } from '../../ui/Text';
import { Progress } from '../../ui/Progress';
import { family, goals } from '../../data/mockData';

type WealthSubTab = 'savings' | 'transfers' | 'card' | 'family' | 'goals';

export const WealthTab = () => {
  const [sub, setSub] = useState<WealthSubTab>('savings');
  const [transferTab, setTransferTab] = useState<'deposit' | 'withdraw'>('deposit');

  const banks = [
    { id: '1', name: 'Chase', last4: '4521', primary: true },
    { id: '2', name: 'Bank of America', last4: '7832', primary: false },
  ];

  const retirement = [
    { type: 'Traditional IRA', balance: 28500, contrib: 4500, limit: 7000 },
    { type: 'Roth IRA', balance: 12300, contrib: 2500, limit: 7000 },
    { type: '401(k)', balance: 87500, contrib: 15000, limit: 23000 },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Navigation */}
      <Card style={{ padding: 8 }}>
        <div style={{ display: 'flex', gap: 6, overflowX: 'auto', paddingBottom: 4 }}>
          <SubTab active={sub === 'savings'} onClick={() => setSub('savings')}>
            Savings
          </SubTab>
          <SubTab active={sub === 'transfers'} onClick={() => setSub('transfers')}>
            Transfers
          </SubTab>
          <SubTab active={sub === 'card'} onClick={() => setSub('card')}>
            Card
          </SubTab>
          <SubTab active={sub === 'family'} onClick={() => setSub('family')}>
            Family
          </SubTab>
          <SubTab active={sub === 'goals'} onClick={() => setSub('goals')}>
            Goals
          </SubTab>
        </div>
      </Card>

      {/* Savings Tab */}
      {sub === 'savings' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card style={{ border: `1px solid ${C.gold}33` }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <Txt c="gray" size={13}>
                  High-Yield Savings
                </Txt>
                <Txt bold size={28} style={{ marginTop: 4 }}>
                  $12,450.00
                </Txt>
                <Badge v="gold" style={{ marginTop: 8 }}>
                  4.5% APY
                </Badge>
              </div>
              <div
                style={{
                  width: 50,
                  height: 50,
                  borderRadius: 25,
                  background: `linear-gradient(135deg, ${C.gold}, ${C.goldLight})`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <span style={{ color: C.bg }}>
                  <Icons.Shield />
                </span>
              </div>
            </div>

            <Inner style={{ marginTop: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <Txt c="gray" size={12}>
                  This Month's Interest
                </Txt>
                <Txt c="green" bold>
                  +$46.88
                </Txt>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Txt c="gray" size={12}>
                  Total Interest Earned
                </Txt>
                <Txt c="gold" bold>
                  $285.42
                </Txt>
              </div>
            </Inner>
          </Card>

          <Card>
            <Txt bold size={16} style={{ marginBottom: 12 }}>
              Retirement Accounts
            </Txt>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {retirement.map((r) => (
                <Inner key={r.type}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <Txt bold size={14}>
                      {r.type}
                    </Txt>
                    <Txt bold size={14}>
                      ${r.balance.toLocaleString()}
                    </Txt>
                  </div>
                  <Progress value={r.contrib} max={r.limit} color={C.green} />
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6 }}>
                    <Txt c="gray" size={11}>
                      ${r.contrib.toLocaleString()} contributed
                    </Txt>
                    <Txt c="gray" size={11}>
                      ${r.limit.toLocaleString()} limit
                    </Txt>
                  </div>
                </Inner>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Transfers Tab */}
      {sub === 'transfers' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card>
            <div style={{ display: 'flex', marginBottom: 16 }}>
              <button
                onClick={() => setTransferTab('deposit')}
                style={{
                  flex: 1,
                  padding: '12px',
                  border: 'none',
                  borderRadius: '10px 0 0 10px',
                  backgroundColor: transferTab === 'deposit' ? C.green : C.inner,
                  color: transferTab === 'deposit' ? C.white : C.gray,
                  fontWeight: 700,
                  cursor: 'pointer',
                }}
              >
                Deposit
              </button>
              <button
                onClick={() => setTransferTab('withdraw')}
                style={{
                  flex: 1,
                  padding: '12px',
                  border: 'none',
                  borderRadius: '0 10px 10px 0',
                  backgroundColor: transferTab === 'withdraw' ? C.red : C.inner,
                  color: transferTab === 'withdraw' ? C.white : C.gray,
                  fontWeight: 700,
                  cursor: 'pointer',
                }}
              >
                Withdraw
              </button>
            </div>

            <div style={{ marginBottom: 16 }}>
              <Txt c="gray" size={12}>
                Amount
              </Txt>
              <Input type="number" placeholder="$0.00" />
            </div>

            <div style={{ marginBottom: 16 }}>
              <Txt c="gray" size={12}>
                From
              </Txt>
              <Inner style={{ marginTop: 6 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ color: C.gold }}>
                      <Icons.Bank />
                    </span>
                    <div>
                      <Txt bold>Chase Checking</Txt>
                      <Txt c="gray" size={12}>
                        ****4521
                      </Txt>
                    </div>
                  </div>
                  <Badge v="success">Primary</Badge>
                </div>
              </Inner>
            </div>

            <GoldBtn full>{transferTab === 'deposit' ? 'Deposit Funds' : 'Withdraw Funds'}</GoldBtn>
          </Card>

          <Card>
            <Txt bold size={16} style={{ marginBottom: 12 }}>
              Linked Accounts
            </Txt>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {banks.map((bank) => (
                <Inner key={bank.id}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span style={{ color: C.gold }}>
                        <Icons.Bank />
                      </span>
                      <div>
                        <Txt bold>{bank.name}</Txt>
                        <Txt c="gray" size={12}>
                          ****{bank.last4}
                        </Txt>
                      </div>
                    </div>
                    {bank.primary && <Badge v="success">Primary</Badge>}
                  </div>
                </Inner>
              ))}
            </div>
            <GoldBtn outline full style={{ marginTop: 12 }}>
              + Link New Account
            </GoldBtn>
          </Card>
        </div>
      )}

      {/* Card Tab */}
      {sub === 'card' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card
            style={{
              background: `linear-gradient(135deg, ${C.gold}, ${C.goldDark})`,
              padding: 20,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 30 }}>
              <Txt bold size={18} style={{ color: C.bg }}>
                ELSON
              </Txt>
              <span style={{ color: C.bg }}>
                <Icons.CreditCard />
              </span>
            </div>
            <Txt size={18} style={{ color: C.bg, letterSpacing: 2 }}>
              •••• •••• •••• 4892
            </Txt>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 20 }}>
              <div>
                <Txt size={10} style={{ color: C.bg, opacity: 0.7 }}>
                  CARD HOLDER
                </Txt>
                <Txt size={12} style={{ color: C.bg }}>
                  ALEX THOMPSON
                </Txt>
              </div>
              <div>
                <Txt size={10} style={{ color: C.bg, opacity: 0.7 }}>
                  EXPIRES
                </Txt>
                <Txt size={12} style={{ color: C.bg }}>
                  12/28
                </Txt>
              </div>
            </div>
          </Card>

          <Card>
            <Txt bold size={16} style={{ marginBottom: 12 }}>
              Card Benefits
            </Txt>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {['2% cashback on all purchases', 'No foreign transaction fees', 'Cell phone protection', 'Extended warranty'].map(
                (benefit) => (
                  <div key={benefit} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ color: C.green }}>
                      <Icons.Check />
                    </span>
                    <Txt size={14}>{benefit}</Txt>
                  </div>
                )
              )}
            </div>
          </Card>
        </div>
      )}

      {/* Family Tab */}
      {sub === 'family' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <Txt bold size={16}>
                Family Members
              </Txt>
              <span style={{ color: C.gold }}>
                <Icons.Plus />
              </span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {family.map((member) => (
                <Inner key={member.id}>
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
                        }}
                      >
                        <span style={{ color: C.gold }}>
                          <Icons.User />
                        </span>
                      </div>
                      <div>
                        <Txt bold size={14}>
                          {member.name}
                        </Txt>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 2 }}>
                          <Badge v={member.status === 'Active' ? 'success' : 'warning'}>{member.role}</Badge>
                          <Txt c="gray" size={11}>
                            {member.accountType}
                          </Txt>
                        </div>
                      </div>
                    </div>
                    <Txt bold size={14}>
                      ${member.balance.toLocaleString()}
                    </Txt>
                  </div>
                </Inner>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Goals Tab */}
      {sub === 'goals' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <Txt bold size={16}>
                Savings Goals
              </Txt>
              <span style={{ color: C.gold }}>
                <Icons.Plus />
              </span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {goals.map((goal) => (
                <Inner key={goal.id}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span style={{ fontSize: 24 }}>{goal.icon}</span>
                      <Txt bold size={14}>
                        {goal.name}
                      </Txt>
                    </div>
                    <Txt c="gold" bold>
                      {((goal.current / goal.target) * 100).toFixed(0)}%
                    </Txt>
                  </div>
                  <Progress value={goal.current} max={goal.target} />
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6 }}>
                    <Txt c="gray" size={11}>
                      ${goal.current.toLocaleString()}
                    </Txt>
                    <Txt c="gray" size={11}>
                      ${goal.target.toLocaleString()}
                    </Txt>
                  </div>
                </Inner>
              ))}
            </div>
          </Card>

          <GoldBtn full>+ Create New Goal</GoldBtn>
        </div>
      )}
    </div>
  );
};
