import React, { useState } from 'react';
import { Link } from 'react-router-dom';

interface PricingPlan {
  name: string;
  price: string;
  period: string;
  description: string;
  features: string[];
  highlighted?: boolean;
  badge?: string;
}

const PricingPage: React.FC = () => {
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'yearly'>('monthly');
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  const plans: PricingPlan[] = [
    {
      name: 'Basic',
      price: billingPeriod === 'monthly' ? '$0' : '$0',
      period: '/month',
      description: 'Perfect for getting started with investing',
      features: [
        'AI-powered portfolio management',
        'Basic stock trading',
        'Round-up investing',
        'Mobile app access',
        'Educational resources',
        'Email support'
      ]
    },
    {
      name: 'Plus',
      price: billingPeriod === 'monthly' ? '$3' : '$30',
      period: billingPeriod === 'monthly' ? '/month' : '/year',
      description: 'For serious investors who want more',
      features: [
        'Everything in Basic',
        'IRA accounts (Traditional & Roth)',
        'Dividend reinvestment',
        'Advanced analytics',
        'Priority support',
        'Custom portfolios'
      ],
      highlighted: true,
      badge: 'Most Popular'
    },
    {
      name: 'Premium',
      price: billingPeriod === 'monthly' ? '$5' : '$50',
      period: billingPeriod === 'monthly' ? '/month' : '/year',
      description: 'Full access to all premium features',
      features: [
        'Everything in Plus',
        'Family accounts (up to 5)',
        'Tax-loss harvesting',
        'Real-time market data',
        'Dedicated advisor',
        'API access',
        'Priority order execution'
      ]
    }
  ];

  const faqs = [
    {
      question: 'Can I switch plans at any time?',
      answer: 'Yes, you can upgrade or downgrade your plan at any time. If you upgrade, you\'ll be prorated for the remainder of your billing period. If you downgrade, the change will take effect at the start of your next billing period.'
    },
    {
      question: 'Is there a minimum investment amount?',
      answer: 'No minimum investment is required to get started. You can begin investing with as little as $5, making it accessible for everyone.'
    },
    {
      question: 'How does the AI-powered investing work?',
      answer: 'Our AI analyzes market trends, your risk tolerance, and investment goals to automatically build and rebalance your portfolio. It continuously monitors and adjusts your investments to optimize returns.'
    },
    {
      question: 'Are my investments protected?',
      answer: 'Yes, your securities are protected up to $500,000 (including up to $250,000 for cash claims) by SIPC. We also use bank-level 256-bit encryption to protect your data.'
    },
    {
      question: 'What is tax-loss harvesting?',
      answer: 'Tax-loss harvesting is a strategy that involves selling investments at a loss to offset capital gains taxes. Our Premium plan includes automated tax-loss harvesting to help maximize your after-tax returns.'
    },
    {
      question: 'How do family accounts work?',
      answer: 'With Premium, you can create up to 5 linked family accounts. These can include custodial accounts for minors, joint accounts, and individual accounts for family members, all managed from a single dashboard.'
    }
  ];

  const comparisonFeatures = [
    { feature: 'AI Portfolio Management', basic: true, plus: true, premium: true },
    { feature: 'Stock Trading', basic: true, plus: true, premium: true },
    { feature: 'Round-Up Investing', basic: true, plus: true, premium: true },
    { feature: 'Mobile App', basic: true, plus: true, premium: true },
    { feature: 'IRA Accounts', basic: false, plus: true, premium: true },
    { feature: 'Dividend Reinvestment', basic: false, plus: true, premium: true },
    { feature: 'Advanced Analytics', basic: false, plus: true, premium: true },
    { feature: 'Family Accounts', basic: false, plus: false, premium: true },
    { feature: 'Tax-Loss Harvesting', basic: false, plus: false, premium: true },
    { feature: 'Real-Time Data', basic: false, plus: false, premium: true },
    { feature: 'Dedicated Advisor', basic: false, plus: false, premium: true },
    { feature: 'API Access', basic: false, plus: false, premium: true },
  ];

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Navigation */}
      <nav className="bg-gray-900 border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <Link to="/" className="flex items-center">
              <div className="h-10 w-10 rounded-lg bg-gradient-to-r from-purple-600 to-blue-500 flex items-center justify-center">
                <span className="text-white font-bold text-xl">E</span>
              </div>
              <span className="ml-3 text-xl font-bold text-white">Elson</span>
            </Link>
            <div className="hidden md:flex items-center space-x-8">
              <Link to="/" className="text-gray-300 hover:text-white transition-colors">Home</Link>
              <Link to="/login" className="text-gray-300 hover:text-white transition-colors">Sign In</Link>
              <Link to="/register" className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors">
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Header */}
      <section className="py-16 text-center">
        <div className="max-w-4xl mx-auto px-4">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Simple, Transparent Pricing
          </h1>
          <p className="text-xl text-gray-400 mb-8">
            Choose the plan that's right for your investment goals. No hidden fees.
          </p>

          {/* Billing Toggle */}
          <div className="flex items-center justify-center gap-4 mb-12">
            <span className={`text-sm ${billingPeriod === 'monthly' ? 'text-white' : 'text-gray-400'}`}>
              Monthly
            </span>
            <button
              onClick={() => setBillingPeriod(billingPeriod === 'monthly' ? 'yearly' : 'monthly')}
              className="relative w-14 h-7 bg-gray-700 rounded-full transition-colors"
            >
              <span
                className={`absolute top-1 w-5 h-5 bg-purple-500 rounded-full transition-transform ${
                  billingPeriod === 'yearly' ? 'translate-x-8' : 'translate-x-1'
                }`}
              />
            </button>
            <span className={`text-sm ${billingPeriod === 'yearly' ? 'text-white' : 'text-gray-400'}`}>
              Yearly
              <span className="ml-2 text-xs bg-green-900 text-green-300 px-2 py-0.5 rounded-full">
                Save 17%
              </span>
            </span>
          </div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="pb-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-3 gap-8">
            {plans.map((plan, index) => (
              <div
                key={index}
                className={`relative rounded-2xl p-8 ${
                  plan.highlighted
                    ? 'bg-gradient-to-b from-purple-900 to-gray-800 border-2 border-purple-500'
                    : 'bg-gray-800 border border-gray-700'
                }`}
              >
                {plan.badge && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    <span className="bg-purple-500 text-white text-sm font-medium px-4 py-1 rounded-full">
                      {plan.badge}
                    </span>
                  </div>
                )}
                <div className="text-center mb-8">
                  <h3 className="text-xl font-semibold text-white mb-2">{plan.name}</h3>
                  <div className="flex items-baseline justify-center gap-1">
                    <span className="text-4xl font-bold text-white">{plan.price}</span>
                    <span className="text-gray-400">{plan.period}</span>
                  </div>
                  <p className="mt-4 text-gray-400 text-sm">{plan.description}</p>
                </div>
                <ul className="space-y-4 mb-8">
                  {plan.features.map((feature, featureIndex) => (
                    <li key={featureIndex} className="flex items-center gap-3">
                      <svg className="h-5 w-5 text-green-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-gray-300 text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>
                <Link
                  to="/register"
                  className={`block w-full text-center py-3 rounded-lg font-medium transition-colors ${
                    plan.highlighted
                      ? 'bg-purple-600 hover:bg-purple-700 text-white'
                      : 'bg-gray-700 hover:bg-gray-600 text-white'
                  }`}
                >
                  {plan.price === '$0' ? 'Start Free' : 'Get Started'}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Feature Comparison */}
      <section className="py-20 bg-gray-800/50">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-white text-center mb-12">
            Compare Plans
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left py-4 px-4 text-gray-400 font-medium">Feature</th>
                  <th className="text-center py-4 px-4 text-white font-medium">Basic</th>
                  <th className="text-center py-4 px-4 text-white font-medium">Plus</th>
                  <th className="text-center py-4 px-4 text-white font-medium">Premium</th>
                </tr>
              </thead>
              <tbody>
                {comparisonFeatures.map((row, index) => (
                  <tr key={index} className="border-b border-gray-700/50">
                    <td className="py-4 px-4 text-gray-300">{row.feature}</td>
                    <td className="text-center py-4 px-4">
                      {row.basic ? (
                        <svg className="h-5 w-5 text-green-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        <svg className="h-5 w-5 text-gray-600 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      )}
                    </td>
                    <td className="text-center py-4 px-4">
                      {row.plus ? (
                        <svg className="h-5 w-5 text-green-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        <svg className="h-5 w-5 text-gray-600 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      )}
                    </td>
                    <td className="text-center py-4 px-4">
                      {row.premium ? (
                        <svg className="h-5 w-5 text-green-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        <svg className="h-5 w-5 text-gray-600 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-20">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-white text-center mb-12">
            Frequently Asked Questions
          </h2>
          <div className="space-y-4">
            {faqs.map((faq, index) => (
              <div
                key={index}
                className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden"
              >
                <button
                  onClick={() => setOpenFaq(openFaq === index ? null : index)}
                  className="w-full flex items-center justify-between p-6 text-left"
                >
                  <span className="font-medium text-white">{faq.question}</span>
                  <svg
                    className={`h-5 w-5 text-gray-400 transition-transform ${
                      openFaq === index ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {openFaq === index && (
                  <div className="px-6 pb-6">
                    <p className="text-gray-400">{faq.answer}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gray-800/50">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold text-white mb-6">
            Ready to Start Investing?
          </h2>
          <p className="text-xl text-gray-400 mb-8">
            Join hundreds of thousands of investors building wealth with Elson.
          </p>
          <Link
            to="/register"
            className="inline-flex items-center justify-center px-8 py-4 text-lg font-medium rounded-lg text-white bg-purple-600 hover:bg-purple-700 transition-colors"
          >
            Create Your Free Account
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-800 border-t border-gray-700 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center mb-4 md:mb-0">
              <div className="h-8 w-8 rounded-lg bg-gradient-to-r from-purple-600 to-blue-500 flex items-center justify-center">
                <span className="text-white font-bold">E</span>
              </div>
              <span className="ml-2 text-lg font-bold text-white">Elson</span>
            </div>
            <p className="text-gray-400 text-sm">
              2025 Elson Technologies. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default PricingPage;
