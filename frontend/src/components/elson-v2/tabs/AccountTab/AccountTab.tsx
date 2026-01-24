import React, { useState } from 'react';
import { C } from '../../primitives/Colors';
import { Icons } from '../../primitives/Icons';
import { Card, Inner } from '../../ui/Card';
import { Badge } from '../../ui/Badge';
import { SubTab, GoldBtn } from '../../ui/Button';
import { Toggle } from '../../ui/Toggle';
import { Input } from '../../ui/Input';
import { Txt } from '../../ui/Text';
import { CircularProgress } from '../../ui/Progress';
import { user, plans } from '../../data/mockData';

type AccountSubTab = 'profile' | 'billing' | 'docs' | 'security' | 'settings' | 'support';

interface AccountTabProps {
  onLogout?: () => void;
}

export const AccountTab = ({ onLogout }: AccountTabProps) => {
  const [sub, setSub] = useState<AccountSubTab>('profile');
  const [twoFactor, setTwoFactor] = useState(true);
  const [biometric, setBiometric] = useState(false);
  const [notifications, setNotifications] = useState({
    trades: true,
    prices: true,
    news: false,
    promotions: false,
  });

  const currentPlan = plans.find((p) => p.name === user.tier) || plans[2];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Navigation */}
      <Card style={{ padding: 8 }}>
        <div style={{ display: 'flex', gap: 6, overflowX: 'auto', paddingBottom: 4 }}>
          <SubTab active={sub === 'profile'} onClick={() => setSub('profile')}>
            Profile
          </SubTab>
          <SubTab active={sub === 'billing'} onClick={() => setSub('billing')}>
            Billing
          </SubTab>
          <SubTab active={sub === 'docs'} onClick={() => setSub('docs')}>
            Docs
          </SubTab>
          <SubTab active={sub === 'security'} onClick={() => setSub('security')}>
            Security
          </SubTab>
          <SubTab active={sub === 'settings'} onClick={() => setSub('settings')}>
            Settings
          </SubTab>
          <SubTab active={sub === 'support'} onClick={() => setSub('support')}>
            Support
          </SubTab>
        </div>
      </Card>

      {/* Profile Tab */}
      {sub === 'profile' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div
                style={{
                  width: 70,
                  height: 70,
                  borderRadius: 35,
                  background: `linear-gradient(135deg, ${C.gold}, ${C.goldLight})`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <span style={{ color: C.bg, fontSize: 28 }}>
                  <Icons.User />
                </span>
              </div>
              <div style={{ flex: 1 }}>
                <Txt bold size={20}>
                  {user.name}
                </Txt>
                <Txt c="gray" size={13}>
                  {user.email}
                </Txt>
                <Badge v="gold" style={{ marginTop: 6 }}>
                  {user.tier}
                </Badge>
              </div>
            </div>
          </Card>

          <Card>
            <Txt bold size={16} style={{ marginBottom: 12 }}>
              Account Info
            </Txt>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <Txt c="gray" size={12}>
                  Full Name
                </Txt>
                <Input defaultValue={user.name} />
              </div>
              <div>
                <Txt c="gray" size={12}>
                  Email
                </Txt>
                <Input defaultValue={user.email} type="email" />
              </div>
              <div>
                <Txt c="gray" size={12}>
                  Phone
                </Txt>
                <Input defaultValue="+1 (555) 123-4567" type="tel" />
              </div>
            </div>
            <GoldBtn full style={{ marginTop: 16 }}>
              Save Changes
            </GoldBtn>
          </Card>

          <Card>
            <Txt bold size={16} style={{ marginBottom: 12 }}>
              Investment Profile
            </Txt>
            <Inner>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                <Txt c="gray">Risk Tolerance</Txt>
                <Badge v="gold">{user.risk}</Badge>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                <Txt c="gray">Investment Goal</Txt>
                <Txt bold>Growth</Txt>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Txt c="gray">Time Horizon</Txt>
                <Txt bold>5-10 years</Txt>
              </div>
            </Inner>
          </Card>
        </div>
      )}

      {/* Billing Tab */}
      {sub === 'billing' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card style={{ border: `1px solid ${C.gold}33` }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <Txt c="gray" size={12}>
                  Current Plan
                </Txt>
                <Txt bold size={24}>
                  {currentPlan.name}
                </Txt>
                <Txt c="gold" bold size={18}>
                  ${currentPlan.price}/mo
                </Txt>
              </div>
              <Badge v="gold">{currentPlan.apy} APY</Badge>
            </div>

            <Inner style={{ marginTop: 16 }}>
              {currentPlan.features.map((feature) => (
                <div key={feature} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <span style={{ color: C.green }}>
                    <Icons.Check />
                  </span>
                  <Txt size={13}>{feature}</Txt>
                </div>
              ))}
            </Inner>
          </Card>

          <Card>
            <Txt bold size={16} style={{ marginBottom: 12 }}>
              Upgrade Plan
            </Txt>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {plans
                .filter((p) => p.price > currentPlan.price)
                .map((plan) => (
                  <Inner
                    key={plan.id}
                    style={{
                      border: plan.popular ? `1px solid ${C.gold}` : undefined,
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <Txt bold size={16}>
                            {plan.name}
                          </Txt>
                          {plan.popular && <Badge v="gold">Popular</Badge>}
                        </div>
                        <Txt c="gray" size={13}>
                          ${plan.price}/mo • {plan.apy} APY
                        </Txt>
                      </div>
                      <GoldBtn outline>Upgrade</GoldBtn>
                    </div>
                  </Inner>
                ))}
            </div>
          </Card>

          <Card>
            <Txt bold size={16} style={{ marginBottom: 12 }}>
              Payment Method
            </Txt>
            <Inner>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ color: C.gold }}>
                    <Icons.CreditCard />
                  </span>
                  <div>
                    <Txt bold>Visa ending in 4892</Txt>
                    <Txt c="gray" size={12}>
                      Expires 12/28
                    </Txt>
                  </div>
                </div>
                <Badge v="success">Default</Badge>
              </div>
            </Inner>
            <GoldBtn outline full style={{ marginTop: 12 }}>
              + Add Payment Method
            </GoldBtn>
          </Card>
        </div>
      )}

      {/* Documents Tab */}
      {sub === 'docs' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card>
            <Txt bold size={16} style={{ marginBottom: 12 }}>
              Monthly Statements
            </Txt>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {['January 2025', 'December 2024', 'November 2024', 'October 2024'].map((month) => (
                <Inner key={month}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span style={{ color: C.gold }}>
                        <Icons.Document />
                      </span>
                      <Txt>{month}</Txt>
                    </div>
                    <span style={{ color: C.gray, cursor: 'pointer' }}>
                      <Icons.Download />
                    </span>
                  </div>
                </Inner>
              ))}
            </div>
          </Card>

          <Card>
            <Txt bold size={16} style={{ marginBottom: 12 }}>
              Tax Documents
            </Txt>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {['Form 1099-B (2024)', 'Form 1099-DIV (2024)', 'Year-End Summary (2024)'].map((doc) => (
                <Inner key={doc}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span style={{ color: C.gold }}>
                        <Icons.Document />
                      </span>
                      <Txt>{doc}</Txt>
                    </div>
                    <span style={{ color: C.gray, cursor: 'pointer' }}>
                      <Icons.Download />
                    </span>
                  </div>
                </Inner>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Security Tab */}
      {sub === 'security' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card>
            <Txt bold size={16} style={{ marginBottom: 16 }}>
              Security Settings
            </Txt>

            <Inner style={{ marginBottom: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <Txt bold>Two-Factor Authentication</Txt>
                  <Txt c="gray" size={12}>
                    Extra security for your account
                  </Txt>
                </div>
                <Toggle on={twoFactor} onToggle={() => setTwoFactor(!twoFactor)} />
              </div>
            </Inner>

            <Inner style={{ marginBottom: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <Txt bold>Biometric Login</Txt>
                  <Txt c="gray" size={12}>
                    Use Face ID or fingerprint
                  </Txt>
                </div>
                <Toggle on={biometric} onToggle={() => setBiometric(!biometric)} />
              </div>
            </Inner>

            <Inner>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <Txt bold>Change Password</Txt>
                  <Txt c="gray" size={12}>
                    Last changed 30 days ago
                  </Txt>
                </div>
                <span style={{ color: C.gold }}>
                  <Icons.Lock />
                </span>
              </div>
            </Inner>
          </Card>

          <Card>
            <Txt bold size={16} style={{ marginBottom: 12 }}>
              Security Score
            </Txt>
            <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
              <div style={{ position: 'relative' }}>
                <CircularProgress value={85} size={80} color={C.green} />
                <div
                  style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                  }}
                >
                  <Txt bold size={20}>
                    85
                  </Txt>
                </div>
              </div>
              <div>
                <Txt c="green" bold>
                  Strong
                </Txt>
                <Txt c="gray" size={12}>
                  Your account is well protected
                </Txt>
              </div>
            </div>
          </Card>

          <Card>
            <Txt bold size={16} style={{ marginBottom: 12 }}>
              Active Sessions
            </Txt>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <Inner style={{ border: `1px solid ${C.green}33` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <Txt bold>This Device</Txt>
                    <Txt c="gray" size={12}>
                      Chrome • San Francisco, CA
                    </Txt>
                  </div>
                  <Badge v="success">Active</Badge>
                </div>
              </Inner>
              <Inner>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <Txt bold>iPhone 15 Pro</Txt>
                    <Txt c="gray" size={12}>
                      iOS App • 2 hours ago
                    </Txt>
                  </div>
                  <Txt c="red" size={12} style={{ cursor: 'pointer' }}>
                    Revoke
                  </Txt>
                </div>
              </Inner>
            </div>
          </Card>
        </div>
      )}

      {/* Settings Tab */}
      {sub === 'settings' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card>
            <Txt bold size={16} style={{ marginBottom: 16 }}>
              Notifications
            </Txt>

            {Object.entries({
              trades: 'Trade Confirmations',
              prices: 'Price Alerts',
              news: 'Market News',
              promotions: 'Promotions',
            }).map(([key, label]) => (
              <Inner key={key} style={{ marginBottom: key === 'promotions' ? 0 : 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Txt>{label}</Txt>
                  <Toggle
                    on={notifications[key as keyof typeof notifications]}
                    onToggle={() =>
                      setNotifications((prev) => ({
                        ...prev,
                        [key]: !prev[key as keyof typeof notifications],
                      }))
                    }
                  />
                </div>
              </Inner>
            ))}
          </Card>

          <Card>
            <Txt bold size={16} style={{ marginBottom: 12 }}>
              Preferences
            </Txt>
            <Inner style={{ marginBottom: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Txt>Theme</Txt>
                <Txt c="gold">Dark</Txt>
              </div>
            </Inner>
            <Inner style={{ marginBottom: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Txt>Currency</Txt>
                <Txt c="gold">USD</Txt>
              </div>
            </Inner>
            <Inner>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Txt>Language</Txt>
                <Txt c="gold">English</Txt>
              </div>
            </Inner>
          </Card>

          <Card style={{ backgroundColor: `${C.red}11`, border: `1px solid ${C.red}33` }}>
            <Txt bold size={16} c="red" style={{ marginBottom: 12 }}>
              Danger Zone
            </Txt>
            <button
              onClick={onLogout}
              style={{
                width: '100%',
                padding: '12px',
                backgroundColor: 'transparent',
                border: `1px solid ${C.red}`,
                borderRadius: 10,
                color: C.red,
                fontWeight: 700,
                cursor: 'pointer',
                marginBottom: 10,
              }}
            >
              Sign Out
            </button>
            <button
              style={{
                width: '100%',
                padding: '12px',
                backgroundColor: C.red,
                border: 'none',
                borderRadius: 10,
                color: C.white,
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              Delete Account
            </button>
          </Card>
        </div>
      )}

      {/* Support Tab */}
      {sub === 'support' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card>
            <Txt bold size={16} style={{ marginBottom: 12 }}>
              Get Help
            </Txt>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                { icon: <Icons.Bot />, title: 'Chat with AI', desc: 'Get instant answers' },
                { icon: <Icons.Document />, title: 'Help Center', desc: 'Browse articles' },
                { icon: <Icons.Send />, title: 'Contact Support', desc: 'Email our team' },
              ].map((item) => (
                <Inner key={item.title} style={{ cursor: 'pointer' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <span style={{ color: C.gold }}>{item.icon}</span>
                    <div>
                      <Txt bold>{item.title}</Txt>
                      <Txt c="gray" size={12}>
                        {item.desc}
                      </Txt>
                    </div>
                  </div>
                </Inner>
              ))}
            </div>
          </Card>

          <Card>
            <Txt bold size={16} style={{ marginBottom: 12 }}>
              FAQ
            </Txt>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                'How do I deposit funds?',
                'What are the trading fees?',
                'How does the AI bot work?',
                'Can I transfer stocks?',
              ].map((q) => (
                <Inner key={q} style={{ cursor: 'pointer' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Txt size={14}>{q}</Txt>
                    <span style={{ color: C.gray }}>›</span>
                  </div>
                </Inner>
              ))}
            </div>
          </Card>

          <Card>
            <Txt c="gray" size={12} style={{ textAlign: 'center' }}>
              Elson v2.0.0 • Build 2025.01
            </Txt>
          </Card>
        </div>
      )}
    </div>
  );
};
