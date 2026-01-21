import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { RootState } from '../store/store';

// Elson Design Components
import { Card, TabGroup, AIInsightRow, PremiumLock } from '../components/elson';
import {
  AIIcon,
  TargetIcon,
  ChartBarIcon,
  LightbulbIcon,
  ShieldIcon,
  LearnIcon,
  DocumentIcon,
  CashIcon,
  LockIcon,
  SendIcon,
} from '../components/icons/ElsonIcons';
import { UserTier, AIInsight } from '../types/elson';

const ElsonAIPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useSelector((state: RootState) => state.auth);
  const [activeTab, setActiveTab] = useState('Chat');
  const [message, setMessage] = useState('');

  // User tier - would come from subscription data in production
  const getUserTier = (): UserTier => 'Growth';
  const userTier = getUserTier();
  const isStarterTier = userTier === 'Starter';

  const tabs = ['Chat', 'Planning', 'Insights', 'Signals', 'Settings'];

  const quickPrompts = [
    "How should I prepare for retirement?",
    "Analyze my portfolio risk",
    "What stocks should I consider?",
    "Help me reduce my tax burden",
  ];

  const planningItems = [
    { icon: TargetIcon, title: 'Retirement Planning', desc: 'Analyze your retirement readiness', color: 'from-green-500/20 to-green-500/10' },
    { icon: LearnIcon, title: 'College Planning', desc: '529 plans & education savings', color: 'from-blue-500/20 to-blue-500/10' },
    { icon: DocumentIcon, title: 'Estate Planning', desc: 'Will, trusts & beneficiaries', color: 'from-purple-500/20 to-purple-500/10' },
    { icon: CashIcon, title: 'Tax Optimization', desc: 'Strategies to reduce tax burden', color: 'from-orange-500/20 to-orange-500/10' },
  ];

  const insights: AIInsight[] = [
    { type: 'buy', symbol: 'NVDA', text: 'Strong momentum with positive sentiment across social and news channels', confidence: 87 },
    { type: 'buy', symbol: 'GOOGL', text: 'Undervalued based on recent earnings beat and AI investments', confidence: 76 },
    { type: 'sell', symbol: 'TSLA', text: 'Sentiment declining 15% this week, consider reducing exposure', confidence: 72 },
    { type: 'alert', text: 'Your tech sector concentration is 45% - consider diversifying', confidence: 95 },
    { type: 'alert', text: 'Cash position at 3% is below recommended 5-10% range', confidence: 88 },
  ];

  const handleSendMessage = () => {
    if (message.trim()) {
      // Would send to AI service
      console.log('Sending message:', message);
      setMessage('');
    }
  };

  return (
    <div className="min-h-screen p-4 md:p-6 space-y-4 md:space-y-6" style={{ backgroundColor: '#0D1B2A' }}>
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
                <AIIcon className="w-5 h-5 text-[#0D1B2A]" />
              </div>
              <div className="flex-1">
                <p className="text-sm text-gray-400 mb-1">Elson AI</p>
                <div
                  className="rounded-2xl rounded-tl-none p-4"
                  style={{ backgroundColor: '#1a2535' }}
                >
                  <p className="text-white">
                    Hello{user?.full_name ? `, ${user.full_name.split(' ')[0]}` : ''}! I'm Elson, your AI financial advisor. I can help you with:
                  </p>
                  <ul className="mt-3 space-y-2 text-gray-300">
                    <li className="flex items-center gap-2">
                      <TargetIcon className="w-4 h-4 text-[#C9A227]" />
                      Retirement & financial planning
                    </li>
                    <li className="flex items-center gap-2">
                      <ChartBarIcon className="w-4 h-4 text-[#C9A227]" />
                      Portfolio analysis & optimization
                    </li>
                    <li className="flex items-center gap-2">
                      <LightbulbIcon className="w-4 h-4 text-[#C9A227]" />
                      Investment insights & recommendations
                    </li>
                    <li className="flex items-center gap-2">
                      <ShieldIcon className="w-4 h-4 text-[#C9A227]" />
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
            {isStarterTier ? (
              <div className="text-center py-4">
                <LockIcon className="w-8 h-8 text-gray-500 mx-auto mb-2" />
                <p className="text-gray-400 mb-2">AI Chat requires Growth tier</p>
                <button
                  onClick={() => navigate('/pricing')}
                  className="px-4 py-2 rounded-lg bg-gradient-to-r from-[#C9A227] to-[#E8D48B] text-[#0D1B2A] text-sm font-semibold"
                >
                  Upgrade to Growth
                </button>
              </div>
            ) : (
              <div className="flex gap-3">
                <input
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder="Ask Elson anything about your finances..."
                  className="flex-1 bg-[#0a1520] border border-gray-700 rounded-xl py-3 px-4 text-white placeholder-gray-500 focus:outline-none focus:border-[#C9A227]/50"
                />
                <button
                  onClick={handleSendMessage}
                  className="px-4 py-3 rounded-xl bg-gradient-to-r from-[#C9A227] to-[#E8D48B] text-[#0D1B2A] font-semibold hover:shadow-lg hover:shadow-[#C9A227]/20 transition-all"
                >
                  <SendIcon className="w-5 h-5" />
                </button>
              </div>
            )}
          </div>
        </Card>
      )}

      {activeTab === 'Planning' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {planningItems.map((item, i) => (
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
            {insights.map((insight, i) => (
              <AIInsightRow key={i} insight={insight} />
            ))}
          </div>
        </Card>
      )}

      {activeTab === 'Signals' && (
        <Card className="p-4">
          {isStarterTier ? (
            <PremiumLock feature="Trading Signals" requiredTier="Growth" onUpgrade={() => navigate('/pricing')}>
              <div className="text-center py-8">
                <ChartBarIcon className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">AI Trading Signals</h3>
                <p className="text-gray-400">Get real-time buy/sell signals based on market analysis</p>
              </div>
            </PremiumLock>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Active Signals</h3>
                <span className="text-xs text-gray-500">Updated 5 min ago</span>
              </div>
              <div className="text-center py-8 text-gray-400">
                No active signals at the moment. Check back during market hours.
              </div>
            </div>
          )}
        </Card>
      )}

      {activeTab === 'Settings' && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-white mb-4">AI Preferences</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 rounded-xl" style={{ backgroundColor: '#1a2535' }}>
              <div>
                <p className="text-sm font-medium text-white">Risk Tolerance</p>
                <p className="text-xs text-gray-500">Adjust AI recommendations based on your risk appetite</p>
              </div>
              <select className="bg-[#0a1520] border border-gray-700 rounded-lg py-2 px-3 text-white text-sm focus:outline-none focus:border-[#C9A227]/50">
                <option>Moderate</option>
                <option>Conservative</option>
                <option>Aggressive</option>
              </select>
            </div>
            <div className="flex items-center justify-between p-4 rounded-xl" style={{ backgroundColor: '#1a2535' }}>
              <div>
                <p className="text-sm font-medium text-white">Notification Frequency</p>
                <p className="text-xs text-gray-500">How often you want to receive AI insights</p>
              </div>
              <select className="bg-[#0a1520] border border-gray-700 rounded-lg py-2 px-3 text-white text-sm focus:outline-none focus:border-[#C9A227]/50">
                <option>Daily</option>
                <option>Hourly</option>
                <option>Real-time</option>
                <option>Weekly</option>
              </select>
            </div>
            <div className="flex items-center justify-between p-4 rounded-xl" style={{ backgroundColor: '#1a2535' }}>
              <div>
                <p className="text-sm font-medium text-white">Auto-Trading Integration</p>
                <p className="text-xs text-gray-500">Allow AI to execute trades automatically</p>
              </div>
              <button
                className="px-4 py-2 rounded-lg text-sm font-medium"
                style={{ backgroundColor: 'rgba(201, 162, 39, 0.2)', color: '#C9A227' }}
              >
                Configure
              </button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default ElsonAIPage;
