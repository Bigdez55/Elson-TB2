import React, { useState, useRef, useEffect } from 'react';
import {
  useWealthAdvisoryQueryMutation,
  AdvisoryMode,
  ServiceTier,
  WealthAdvisoryResponse,
  Citation,
  ProfessionalRole,
} from '../../services/wealthAdvisoryApi';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  citations?: Citation[];
  professionals?: ProfessionalRole[];
  nextSteps?: string[];
  confidence?: number;
}

interface WealthAdvisoryChatProps {
  userTier?: ServiceTier;
  initialMode?: AdvisoryMode;
  onProfessionalClick?: (role: ProfessionalRole) => void;
}

const ADVISORY_MODE_OPTIONS: { value: AdvisoryMode; label: string; icon: string }[] = [
  { value: 'general', label: 'General Advisory', icon: '💼' },
  { value: 'estate_planning', label: 'Estate Planning', icon: '🏛️' },
  { value: 'investment_advisory', label: 'Investment', icon: '📈' },
  { value: 'tax_optimization', label: 'Tax Planning', icon: '📊' },
  { value: 'succession_planning', label: 'Succession', icon: '🔄' },
  { value: 'family_governance', label: 'Family Governance', icon: '👨‍👩‍👧‍👦' },
  { value: 'trust_administration', label: 'Trust Admin', icon: '📜' },
  { value: 'credit_financing', label: 'Credit & Financing', icon: '💳' },
  { value: 'compliance_operations', label: 'Compliance', icon: '✅' },
];

const TIER_LABELS: Record<ServiceTier, string> = {
  foundation: 'Foundation ($0-10K)',
  builder: 'Builder ($10K-75K)',
  growth: 'Growth ($75K-500K)',
  affluent: 'Affluent ($500K-5M)',
  hnw_uhnw: 'HNW/UHNW ($5M+)',
};

const WealthAdvisoryChat: React.FC<WealthAdvisoryChatProps> = ({
  userTier = 'foundation',
  initialMode = 'general',
  onProfessionalClick,
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [advisoryMode, setAdvisoryMode] = useState<AdvisoryMode>(initialMode);
  const [showCitations, setShowCitations] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [sendQuery, { isLoading }] = useWealthAdvisoryQueryMutation();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Add welcome message on mount
  useEffect(() => {
    const welcomeMessage: Message = {
      id: 'welcome',
      role: 'assistant',
      content: `Welcome to Elson Financial AI! I'm your personal wealth management advisor with expertise spanning CFP, CFA, CPA, CPWA, and estate planning.

I can help you with:
- Estate planning and trust administration
- Investment strategy and portfolio analysis
- Tax optimization and planning
- Business succession planning
- Family governance and wealth transfer
- Credit and financing options

Select an advisory mode above or ask me anything about wealth management. Your current service tier (${TIER_LABELS[userTier]}) gives you access to comprehensive financial planning guidance.

How can I assist you today?`,
      timestamp: new Date(),
    };
    setMessages([welcomeMessage]);
  }, [userTier]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');

    try {
      const response = await sendQuery({
        query: inputValue,
        advisory_mode: advisoryMode,
        include_citations: showCitations,
        user_tier: userTier,
      }).unwrap();

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
        citations: response.citations,
        professionals: response.recommended_professionals,
        nextSteps: response.next_steps,
        confidence: response.confidence,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'I apologize, but I encountered an error processing your request. Please try again or rephrase your question.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  const renderMessage = (message: Message) => {
    const isUser = message.role === 'user';

    return (
      <div
        key={message.id}
        className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
      >
        <div
          className={`max-w-3xl rounded-lg p-4 ${
            isUser
              ? 'bg-purple-600 text-white'
              : 'bg-gray-700 text-gray-100'
          }`}
        >
          {/* Message content */}
          <div className="whitespace-pre-wrap">{message.content}</div>

          {/* Confidence indicator */}
          {message.confidence !== undefined && (
            <div className="mt-2 flex items-center text-sm text-gray-400">
              <span className="mr-2">Confidence:</span>
              <div className="w-24 bg-gray-600 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    message.confidence > 0.8
                      ? 'bg-green-500'
                      : message.confidence > 0.6
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
                  }`}
                  style={{ width: `${message.confidence * 100}%` }}
                />
              </div>
              <span className="ml-2">{Math.round(message.confidence * 100)}%</span>
            </div>
          )}

          {/* Next steps */}
          {message.nextSteps && message.nextSteps.length > 0 && (
            <div className="mt-4 p-3 bg-gray-800 rounded-lg">
              <h4 className="text-sm font-semibold text-purple-400 mb-2">
                Recommended Next Steps:
              </h4>
              <ul className="list-disc list-inside text-sm text-gray-300 space-y-1">
                {message.nextSteps.map((step, idx) => (
                  <li key={idx}>{step}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommended professionals */}
          {message.professionals && message.professionals.length > 0 && (
            <div className="mt-4 p-3 bg-gray-800 rounded-lg">
              <h4 className="text-sm font-semibold text-purple-400 mb-2">
                Recommended Professionals:
              </h4>
              <div className="flex flex-wrap gap-2">
                {message.professionals.map((prof, idx) => (
                  <button
                    key={idx}
                    onClick={() => onProfessionalClick?.(prof)}
                    className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded-full text-sm text-gray-200 transition-colors"
                  >
                    {prof.title}
                    {prof.credentials.length > 0 && (
                      <span className="ml-1 text-gray-400">
                        ({prof.credentials[0]})
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Citations */}
          {showCitations && message.citations && message.citations.length > 0 && (
            <div className="mt-4 border-t border-gray-600 pt-3">
              <h4 className="text-xs font-semibold text-gray-400 mb-2">
                Sources ({message.citations.length}):
              </h4>
              <div className="space-y-2">
                {message.citations.slice(0, 3).map((citation, idx) => (
                  <div
                    key={idx}
                    className="text-xs p-2 bg-gray-800 rounded"
                  >
                    <div className="flex justify-between items-start">
                      <span className="font-medium text-purple-300">
                        {citation.category}
                      </span>
                      <span className="text-gray-500">
                        {Math.round(citation.relevance_score * 100)}% match
                      </span>
                    </div>
                    <p className="text-gray-400 mt-1 line-clamp-2">
                      {citation.content_preview}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Timestamp */}
          <div className="mt-2 text-xs text-gray-500">
            {message.timestamp.toLocaleTimeString()}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-gray-800 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="p-4 bg-gray-900 border-b border-gray-700">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center">
            <span className="text-2xl mr-3">🎯</span>
            <div>
              <h2 className="text-lg font-bold text-white">
                Wealth Advisory AI
              </h2>
              <p className="text-sm text-gray-400">
                {TIER_LABELS[userTier]}
              </p>
            </div>
          </div>
          <label className="flex items-center text-sm text-gray-400">
            <input
              type="checkbox"
              checked={showCitations}
              onChange={(e) => setShowCitations(e.target.checked)}
              className="mr-2 rounded"
            />
            Show sources
          </label>
        </div>

        {/* Advisory mode selector */}
        <div className="flex flex-wrap gap-2">
          {ADVISORY_MODE_OPTIONS.map((mode) => (
            <button
              key={mode.value}
              onClick={() => setAdvisoryMode(mode.value)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                advisoryMode === mode.value
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              <span className="mr-1">{mode.icon}</span>
              {mode.label}
            </button>
          ))}
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map(renderMessage)}
        {isLoading && (
          <div className="flex justify-start mb-4">
            <div className="bg-gray-700 rounded-lg p-4 flex items-center">
              <div className="animate-pulse flex space-x-2">
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce delay-100" />
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce delay-200" />
              </div>
              <span className="ml-3 text-gray-400">
                Consulting wealth management expertise...
              </span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <form onSubmit={handleSubmit} className="p-4 bg-gray-900 border-t border-gray-700">
        <div className="flex space-x-3">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask about estate planning, investments, taxes, succession..."
            className="flex-1 bg-gray-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !inputValue.trim()}
            className="px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
          >
            {isLoading ? 'Thinking...' : 'Send'}
          </button>
        </div>
        <p className="mt-2 text-xs text-gray-500 text-center">
          Powered by Elson Financial AI with 70+ professional roles
        </p>
      </form>
    </div>
  );
};

export default WealthAdvisoryChat;
