import React, { useState } from 'react';

interface InsuranceProduct {
  id: string;
  name: string;
  type: 'Life' | 'Disability' | 'Critical Illness';
  monthlyPremium: number;
  coverage: number;
  features: string[];
  icon: string;
}

interface Quote {
  age: number;
  coverage: number;
  term: number;
  monthlyPremium: number;
}

const InsurancePage: React.FC = () => {
  const [selectedType, setSelectedType] = useState<'life' | 'disability' | 'critical'>('life');
  const [quoteAge, setQuoteAge] = useState<string>('30');
  const [quoteCoverage, setQuoteCoverage] = useState<string>('500000');
  const [quoteTerm, setQuoteTerm] = useState<string>('20');

  const insuranceProducts: InsuranceProduct[] = [
    {
      id: '1',
      name: 'Term Life Insurance',
      type: 'Life',
      monthlyPremium: 45,
      coverage: 500000,
      features: [
        'Affordable coverage for a specific term',
        'Level premiums for the entire term',
        'Convertible to permanent insurance',
        'No medical exam required (under $500K)',
      ],
      icon: '🛡️',
    },
    {
      id: '2',
      name: 'Whole Life Insurance',
      type: 'Life',
      monthlyPremium: 185,
      coverage: 250000,
      features: [
        'Lifetime coverage guaranteed',
        'Cash value accumulation',
        'Fixed premiums never increase',
        'Dividends may be available',
      ],
      icon: '💎',
    },
    {
      id: '3',
      name: 'Short-Term Disability',
      type: 'Disability',
      monthlyPremium: 28,
      coverage: 60000,
      features: [
        'Covers 60% of income',
        'Benefits begin after 14 days',
        'Coverage up to 24 months',
        'Covers illness and injury',
      ],
      icon: '🏥',
    },
    {
      id: '4',
      name: 'Long-Term Disability',
      type: 'Disability',
      monthlyPremium: 52,
      coverage: 120000,
      features: [
        'Covers 60% of income',
        'Benefits until age 65',
        'Own occupation definition',
        'Cost of living adjustments',
      ],
      icon: '🦽',
    },
    {
      id: '5',
      name: 'Critical Illness',
      type: 'Critical Illness',
      monthlyPremium: 38,
      coverage: 100000,
      features: [
        'Lump sum payment upon diagnosis',
        'Covers 30+ critical illnesses',
        'Use funds for any purpose',
        'No restrictions on treatment',
      ],
      icon: '❤️',
    },
  ];

  const filteredProducts = insuranceProducts.filter((product) => {
    if (selectedType === 'life') return product.type === 'Life';
    if (selectedType === 'disability') return product.type === 'Disability';
    if (selectedType === 'critical') return product.type === 'Critical Illness';
    return true;
  });

  const calculateQuote = (): Quote => {
    const age = parseInt(quoteAge) || 30;
    const coverage = parseInt(quoteCoverage) || 500000;
    const term = parseInt(quoteTerm) || 20;

    // Simple calculation (not actuarially accurate)
    const baseRate = 0.0001;
    const ageFactor = 1 + (age - 25) * 0.02;
    const coverageFactor = coverage / 100000;
    const termFactor = 1 + (30 - term) * 0.01;

    const monthlyPremium = baseRate * coverageFactor * ageFactor * termFactor * coverage;

    return {
      age,
      coverage,
      term,
      monthlyPremium: Math.round(monthlyPremium * 100) / 100,
    };
  };

  const quote = calculateQuote();

  return (
    <div className="bg-gray-800 min-h-screen p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Insurance Protection</h1>
        <p className="text-gray-400">
          Protect what matters most with comprehensive life, disability, and critical illness coverage
        </p>
      </div>

      {/* Category Tabs */}
      <div className="mb-6">
        <div className="flex space-x-2 bg-gray-900 p-2 rounded-lg inline-flex">
          <button
            onClick={() => setSelectedType('life')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              selectedType === 'life' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:bg-gray-800'
            }`}
          >
            🛡️ Life Insurance
          </button>
          <button
            onClick={() => setSelectedType('disability')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              selectedType === 'disability' ? 'bg-purple-600 text-white' : 'text-gray-400 hover:bg-gray-800'
            }`}
          >
            🏥 Disability
          </button>
          <button
            onClick={() => setSelectedType('critical')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              selectedType === 'critical' ? 'bg-pink-600 text-white' : 'text-gray-400 hover:bg-gray-800'
            }`}
          >
            ❤️ Critical Illness
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Products List */}
        <div className="lg:col-span-2 space-y-6">
          {filteredProducts.map((product) => (
            <div key={product.id} className="bg-gray-900 rounded-xl p-6 hover:bg-gray-850 transition-colors">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-4">
                  <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-500 rounded-lg flex items-center justify-center flex-shrink-0">
                    <span className="text-3xl">{product.icon}</span>
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-white">{product.name}</h3>
                    <p className="text-sm text-gray-400">{product.type} Insurance</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-white">${product.monthlyPremium}/mo</div>
                  <div className="text-sm text-gray-400">${product.coverage.toLocaleString()} coverage</div>
                </div>
              </div>

              <div className="space-y-2 mb-4">
                {product.features.map((feature, index) => (
                  <div key={index} className="flex items-start space-x-2 text-gray-300 text-sm">
                    <span className="text-green-400 mt-0.5">✓</span>
                    <span>{feature}</span>
                  </div>
                ))}
              </div>

              <div className="flex space-x-3">
                <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg font-medium transition-colors">
                  Get Quote
                </button>
                <button className="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-2 rounded-lg font-medium transition-colors">
                  Learn More
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Quick Quote Calculator */}
          <div className="bg-gradient-to-br from-blue-900 to-indigo-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-4">📊 Quick Quote</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-blue-200 mb-2">Your Age</label>
                <input
                  type="number"
                  value={quoteAge}
                  onChange={(e) => setQuoteAge(e.target.value)}
                  className="w-full bg-white/10 backdrop-blur text-white px-4 py-2 rounded-lg border border-blue-500/30 focus:border-blue-500 focus:outline-none"
                  placeholder="30"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-blue-200 mb-2">Coverage Amount</label>
                <select
                  value={quoteCoverage}
                  onChange={(e) => setQuoteCoverage(e.target.value)}
                  className="w-full bg-white/10 backdrop-blur text-white px-4 py-2 rounded-lg border border-blue-500/30 focus:border-blue-500 focus:outline-none"
                >
                  <option value="250000">$250,000</option>
                  <option value="500000">$500,000</option>
                  <option value="750000">$750,000</option>
                  <option value="1000000">$1,000,000</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-blue-200 mb-2">Term Length</label>
                <select
                  value={quoteTerm}
                  onChange={(e) => setQuoteTerm(e.target.value)}
                  className="w-full bg-white/10 backdrop-blur text-white px-4 py-2 rounded-lg border border-blue-500/30 focus:border-blue-500 focus:outline-none"
                >
                  <option value="10">10 years</option>
                  <option value="20">20 years</option>
                  <option value="30">30 years</option>
                </select>
              </div>

              <div className="bg-white/10 backdrop-blur rounded-lg p-4 border border-blue-500/30">
                <div className="text-blue-200 text-sm mb-1">Estimated Premium</div>
                <div className="text-3xl font-bold text-white mb-2">${quote.monthlyPremium}/mo</div>
                <div className="text-xs text-blue-200">
                  ${(quote.monthlyPremium * 12).toFixed(2)}/year
                </div>
              </div>

              <button className="w-full bg-white hover:bg-blue-50 text-blue-900 py-3 rounded-lg font-medium transition-colors">
                Get Personalized Quote
              </button>
            </div>
          </div>

          {/* Why Insurance */}
          <div className="bg-gray-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-3">💡 Why Insurance?</h3>
            <div className="space-y-3 text-sm text-gray-300">
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="font-medium text-white mb-1">Protect Your Family</div>
                <p className="text-xs text-gray-400">Ensure financial security for loved ones</p>
              </div>
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="font-medium text-white mb-1">Income Replacement</div>
                <p className="text-xs text-gray-400">Replace lost income from disability</p>
              </div>
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="font-medium text-white mb-1">Debt Coverage</div>
                <p className="text-xs text-gray-400">Pay off mortgage and debts</p>
              </div>
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="font-medium text-white mb-1">Peace of Mind</div>
                <p className="text-xs text-gray-400">Financial protection when needed most</p>
              </div>
            </div>
          </div>

          {/* Coverage Calculator */}
          <div className="bg-gray-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-3">📈 Coverage Needed</h3>
            <p className="text-sm text-gray-400 mb-4">
              Financial experts recommend 10-12x your annual income
            </p>
            <div className="space-y-3">
              <div className="flex items-center justify-between bg-gray-800 p-3 rounded-lg">
                <span className="text-gray-300 text-sm">Annual Income</span>
                <span className="text-white font-semibold">$75,000</span>
              </div>
              <div className="flex items-center justify-between bg-gray-800 p-3 rounded-lg">
                <span className="text-gray-300 text-sm">Multiplier (10x)</span>
                <span className="text-white font-semibold">10x</span>
              </div>
              <div className="flex items-center justify-between bg-gradient-to-r from-blue-900/50 to-purple-900/50 p-3 rounded-lg border border-blue-600/30">
                <span className="text-blue-300 font-medium">Recommended</span>
                <span className="text-blue-400 font-bold text-lg">$750,000</span>
              </div>
            </div>
          </div>

          {/* Benefits */}
          <div className="bg-gradient-to-br from-purple-900 to-pink-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-3">✨ Elson Benefits</h3>
            <div className="space-y-2 text-sm text-gray-200">
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>Up to 15% discount for Elson members</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>Fast approval process</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>No medical exam required (under $500K)</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>Free policy review with experts</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>✓</span>
                <p>Bundle discounts available</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InsurancePage;
