import React from 'react';

/**
 * Consolidated Portfolio Analytics component that combines:
 * - Portfolio Analytics
 * - Performance Analytics
 * - Risk Analytics
 * - Correlation Analytics
 */
const PortfolioAnalytics: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Portfolio Analytics</h1>
      </div>

      {/* Portfolio overview stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-gray-400 text-sm">Total Value</h3>
          <p className="text-2xl font-bold mt-1">$142,892.19</p>
          <p className="text-sm text-gray-400">+14.3% YTD</p>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-gray-400 text-sm">Risk Score</h3>
          <p className="text-2xl font-bold mt-1 text-yellow-500">68</p>
          <p className="text-sm text-gray-400">Moderate Risk</p>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-gray-400 text-sm">Diversification</h3>
          <p className="text-2xl font-bold mt-1 text-green-500">87%</p>
          <p className="text-sm text-gray-400">Well-diversified</p>
        </div>
      </div>

      {/* Asset Allocation */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h2 className="text-xl font-semibold mb-4">Asset Allocation</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="flex items-center justify-center">
            <div className="w-48 h-48 rounded-full border-8 border-gray-700 relative flex items-center justify-center">
              <div className="absolute inset-0" style={{ background: 'conic-gradient(#4F46E5 0% 35%, #10B981 35% 55%, #F59E0B 55% 70%, #EF4444 70% 85%, #8B5CF6 85% 100%)' }}></div>
              <div className="w-28 h-28 bg-gray-800 rounded-full z-10"></div>
            </div>
          </div>
          <div>
            <div className="space-y-2">
              <div className="flex items-center">
                <span className="w-4 h-4 bg-indigo-600 mr-2"></span>
                <span>Technology (35%)</span>
              </div>
              <div className="flex items-center">
                <span className="w-4 h-4 bg-green-600 mr-2"></span>
                <span>Financial Services (20%)</span>
              </div>
              <div className="flex items-center">
                <span className="w-4 h-4 bg-yellow-600 mr-2"></span>
                <span>Healthcare (15%)</span>
              </div>
              <div className="flex items-center">
                <span className="w-4 h-4 bg-red-600 mr-2"></span>
                <span>Consumer Discretionary (15%)</span>
              </div>
              <div className="flex items-center">
                <span className="w-4 h-4 bg-purple-600 mr-2"></span>
                <span>Other Sectors (15%)</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h2 className="text-xl font-semibold mb-4">Performance Metrics</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-3 border border-gray-700 rounded">
            <p className="text-sm text-gray-400">Alpha</p>
            <p className="text-xl font-bold text-green-500">3.42%</p>
          </div>
          <div className="text-center p-3 border border-gray-700 rounded">
            <p className="text-sm text-gray-400">Beta</p>
            <p className="text-xl font-bold">1.12</p>
          </div>
          <div className="text-center p-3 border border-gray-700 rounded">
            <p className="text-sm text-gray-400">Sharpe Ratio</p>
            <p className="text-xl font-bold text-green-500">1.87</p>
          </div>
          <div className="text-center p-3 border border-gray-700 rounded">
            <p className="text-sm text-gray-400">Max Drawdown</p>
            <p className="text-xl font-bold text-red-500">12.3%</p>
          </div>
          <div className="text-center p-3 border border-gray-700 rounded">
            <p className="text-sm text-gray-400">Volatility</p>
            <p className="text-xl font-bold">15.7%</p>
          </div>
          <div className="text-center p-3 border border-gray-700 rounded">
            <p className="text-sm text-gray-400">Sortino Ratio</p>
            <p className="text-xl font-bold text-green-500">2.12</p>
          </div>
          <div className="text-center p-3 border border-gray-700 rounded">
            <p className="text-sm text-gray-400">Information Ratio</p>
            <p className="text-xl font-bold text-green-500">1.45</p>
          </div>
          <div className="text-center p-3 border border-gray-700 rounded">
            <p className="text-sm text-gray-400">Tracking Error</p>
            <p className="text-xl font-bold">3.26%</p>
          </div>
        </div>
      </div>

      {/* Risk Analysis */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h2 className="text-xl font-semibold mb-4">Risk Analysis</h2>
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-medium mb-2">Value at Risk (VaR)</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-3 border border-gray-700 rounded">
                <p className="text-sm text-gray-400">Daily (95%)</p>
                <p className="text-xl font-bold text-yellow-500">$1,586</p>
              </div>
              <div className="text-center p-3 border border-gray-700 rounded">
                <p className="text-sm text-gray-400">Weekly (95%)</p>
                <p className="text-xl font-bold text-yellow-500">$3,742</p>
              </div>
              <div className="text-center p-3 border border-gray-700 rounded">
                <p className="text-sm text-gray-400">Monthly (95%)</p>
                <p className="text-xl font-bold text-yellow-500">$7,915</p>
              </div>
            </div>
          </div>
          
          <div>
            <h3 className="text-lg font-medium mb-2">Stress Tests</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-3 border border-gray-700 rounded">
                <p className="text-sm text-gray-400">Market Drop (20%)</p>
                <p className="text-xl font-bold text-red-500">-$25,432</p>
                <p className="text-sm text-gray-400">-17.8% impact</p>
              </div>
              <div className="p-3 border border-gray-700 rounded">
                <p className="text-sm text-gray-400">Tech Sector Crash</p>
                <p className="text-xl font-bold text-red-500">-$19,876</p>
                <p className="text-sm text-gray-400">-13.9% impact</p>
              </div>
              <div className="p-3 border border-gray-700 rounded">
                <p className="text-sm text-gray-400">Interest Rate Hike</p>
                <p className="text-xl font-bold text-red-500">-$8,254</p>
                <p className="text-sm text-gray-400">-5.8% impact</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Correlation Analysis */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h2 className="text-xl font-semibold mb-4">Correlation Analysis</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left pb-2 pr-4">Asset</th>
                <th className="text-left pb-2 px-4">AAPL</th>
                <th className="text-left pb-2 px-4">MSFT</th>
                <th className="text-left pb-2 px-4">AMZN</th>
                <th className="text-left pb-2 px-4">TSLA</th>
                <th className="text-left pb-2 px-4">JPM</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="py-2 pr-4 font-medium">AAPL</td>
                <td className="py-2 px-4">1.00</td>
                <td className="py-2 px-4 text-yellow-500">0.65</td>
                <td className="py-2 px-4 text-yellow-500">0.58</td>
                <td className="py-2 px-4 text-green-500">0.42</td>
                <td className="py-2 px-4 text-green-500">0.35</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-medium">MSFT</td>
                <td className="py-2 px-4 text-yellow-500">0.65</td>
                <td className="py-2 px-4">1.00</td>
                <td className="py-2 px-4 text-yellow-500">0.72</td>
                <td className="py-2 px-4 text-green-500">0.38</td>
                <td className="py-2 px-4 text-green-500">0.41</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-medium">AMZN</td>
                <td className="py-2 px-4 text-yellow-500">0.58</td>
                <td className="py-2 px-4 text-yellow-500">0.72</td>
                <td className="py-2 px-4">1.00</td>
                <td className="py-2 px-4 text-yellow-500">0.56</td>
                <td className="py-2 px-4 text-green-500">0.32</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-medium">TSLA</td>
                <td className="py-2 px-4 text-green-500">0.42</td>
                <td className="py-2 px-4 text-green-500">0.38</td>
                <td className="py-2 px-4 text-yellow-500">0.56</td>
                <td className="py-2 px-4">1.00</td>
                <td className="py-2 px-4 text-green-500">0.24</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-medium">JPM</td>
                <td className="py-2 px-4 text-green-500">0.35</td>
                <td className="py-2 px-4 text-green-500">0.41</td>
                <td className="py-2 px-4 text-green-500">0.32</td>
                <td className="py-2 px-4 text-green-500">0.24</td>
                <td className="py-2 px-4">1.00</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div className="mt-4">
          <p className="text-sm text-gray-400">
            <span className="inline-block w-3 h-3 bg-red-500 mr-1"></span> High correlation (0.8-1.0)
            <span className="inline-block w-3 h-3 bg-yellow-500 ml-4 mr-1"></span> Medium correlation (0.5-0.8) 
            <span className="inline-block w-3 h-3 bg-green-500 ml-4 mr-1"></span> Low correlation (0.0-0.5)
          </p>
        </div>
      </div>
    </div>
  );
};

export default PortfolioAnalytics;