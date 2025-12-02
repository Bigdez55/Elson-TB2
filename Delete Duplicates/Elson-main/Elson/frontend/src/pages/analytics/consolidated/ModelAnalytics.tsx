import React from 'react';

/**
 * Consolidated Model Analytics component that combines:
 * - Model Performance Analytics
 * - Prediction Analytics
 * - Strategy Analytics
 * - Backtesting Analytics
 */
const ModelAnalytics: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Model Performance Analytics</h1>
      </div>

      {/* Model Performance Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-gray-400 text-sm">Overall Accuracy</h3>
          <p className="text-2xl font-bold mt-1 text-green-500">73.1%</p>
          <p className="text-sm text-gray-400">+4.2% from last month</p>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-gray-400 text-sm">Active Models</h3>
          <p className="text-2xl font-bold mt-1">8</p>
          <p className="text-sm text-gray-400">3 hybrid models</p>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-gray-400 text-sm">Daily Predictions</h3>
          <p className="text-2xl font-bold mt-1">1,287</p>
          <p className="text-sm text-gray-400">across 156 assets</p>
        </div>
      </div>

      {/* Model Comparison */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h2 className="text-xl font-semibold mb-4">Model Comparison</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left pb-2">Model</th>
                <th className="text-left pb-2">Type</th>
                <th className="text-left pb-2">Accuracy</th>
                <th className="text-left pb-2">Win Rate</th>
                <th className="text-left pb-2">Avg. Return</th>
                <th className="text-left pb-2">Max Drawdown</th>
                <th className="text-left pb-2">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-gray-700">
                <td className="py-3">
                  <div className="font-medium">Quantum Regression</div>
                  <div className="text-xs text-gray-400">v2.3.5</div>
                </td>
                <td className="py-3">Quantum</td>
                <td className="py-3 text-green-500">78.2%</td>
                <td className="py-3 text-green-500">73.1%</td>
                <td className="py-3 text-green-500">0.84%</td>
                <td className="py-3 text-yellow-500">14.7%</td>
                <td className="py-3">
                  <span className="px-2 py-1 bg-green-900 text-green-300 rounded-full text-xs">Active</span>
                </td>
              </tr>
              <tr className="border-b border-gray-700">
                <td className="py-3">
                  <div className="font-medium">Hybrid LSTM-Quantum</div>
                  <div className="text-xs text-gray-400">v1.8.2</div>
                </td>
                <td className="py-3">Hybrid</td>
                <td className="py-3 text-green-500">75.9%</td>
                <td className="py-3 text-green-500">71.3%</td>
                <td className="py-3 text-green-500">0.79%</td>
                <td className="py-3 text-yellow-500">12.3%</td>
                <td className="py-3">
                  <span className="px-2 py-1 bg-green-900 text-green-300 rounded-full text-xs">Active</span>
                </td>
              </tr>
              <tr className="border-b border-gray-700">
                <td className="py-3">
                  <div className="font-medium">Volatility Regime Switching</div>
                  <div className="text-xs text-gray-400">v3.1.0</div>
                </td>
                <td className="py-3">Classical</td>
                <td className="py-3 text-green-500">69.8%</td>
                <td className="py-3 text-yellow-500">64.5%</td>
                <td className="py-3 text-yellow-500">0.67%</td>
                <td className="py-3 text-green-500">8.4%</td>
                <td className="py-3">
                  <span className="px-2 py-1 bg-green-900 text-green-300 rounded-full text-xs">Active</span>
                </td>
              </tr>
              <tr className="border-b border-gray-700">
                <td className="py-3">
                  <div className="font-medium">Deep NLP Sentiment</div>
                  <div className="text-xs text-gray-400">v2.0.1</div>
                </td>
                <td className="py-3">NLP</td>
                <td className="py-3 text-yellow-500">62.3%</td>
                <td className="py-3 text-yellow-500">58.9%</td>
                <td className="py-3 text-yellow-500">0.52%</td>
                <td className="py-3 text-green-500">9.7%</td>
                <td className="py-3">
                  <span className="px-2 py-1 bg-green-900 text-green-300 rounded-full text-xs">Active</span>
                </td>
              </tr>
              <tr>
                <td className="py-3">
                  <div className="font-medium">GA Adaptive Strategy</div>
                  <div className="text-xs text-gray-400">v1.4.6</div>
                </td>
                <td className="py-3">Evolutionary</td>
                <td className="py-3 text-red-500">55.7%</td>
                <td className="py-3 text-red-500">52.1%</td>
                <td className="py-3 text-red-500">0.23%</td>
                <td className="py-3 text-red-500">18.2%</td>
                <td className="py-3">
                  <span className="px-2 py-1 bg-red-900 text-red-300 rounded-full text-xs">Paused</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Performance by Market Regime */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h2 className="text-xl font-semibold mb-4">Performance by Market Regime</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="border border-gray-700 rounded-lg p-4">
            <h3 className="text-lg font-medium mb-3">Low Volatility</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-400">Quantum Model</span>
                <span className="text-green-500">68.4%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Hybrid Model</span>
                <span className="text-green-500">65.2%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Ensemble Strategy</span>
                <span className="text-green-500">71.7%</span>
              </div>
              <div className="mt-4 pt-3 border-t border-gray-700">
                <div className="flex justify-between">
                  <span className="font-medium">Avg. Win Rate</span>
                  <span className="font-medium text-green-500">68.4%</span>
                </div>
              </div>
            </div>
          </div>
          
          <div className="border border-gray-700 rounded-lg p-4">
            <h3 className="text-lg font-medium mb-3">Medium Volatility</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-400">Quantum Model</span>
                <span className="text-green-500">72.8%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Hybrid Model</span>
                <span className="text-green-500">70.5%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Ensemble Strategy</span>
                <span className="text-green-500">75.2%</span>
              </div>
              <div className="mt-4 pt-3 border-t border-gray-700">
                <div className="flex justify-between">
                  <span className="font-medium">Avg. Win Rate</span>
                  <span className="font-medium text-green-500">72.8%</span>
                </div>
              </div>
            </div>
          </div>
          
          <div className="border border-gray-700 rounded-lg p-4">
            <h3 className="text-lg font-medium mb-3">High Volatility</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-400">Quantum Model</span>
                <span className="text-green-500">73.1%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Hybrid Model</span>
                <span className="text-green-500">76.4%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Ensemble Strategy</span>
                <span className="text-green-500">74.8%</span>
              </div>
              <div className="mt-4 pt-3 border-t border-gray-700">
                <div className="flex justify-between">
                  <span className="font-medium">Avg. Win Rate</span>
                  <span className="font-medium text-green-500">74.8%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Backtesting Results */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h2 className="text-xl font-semibold mb-4">Backtesting Results</h2>
        <div className="space-y-6">
          <div className="h-72 bg-gray-700 rounded-lg flex items-center justify-center">
            [Equity Curve Chart Placeholder]
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-3 border border-gray-700 rounded">
              <p className="text-sm text-gray-400">Total Return</p>
              <p className="text-xl font-bold text-green-500">142.8%</p>
            </div>
            <div className="text-center p-3 border border-gray-700 rounded">
              <p className="text-sm text-gray-400">Annual Return</p>
              <p className="text-xl font-bold text-green-500">24.7%</p>
            </div>
            <div className="text-center p-3 border border-gray-700 rounded">
              <p className="text-sm text-gray-400">Sharpe Ratio</p>
              <p className="text-xl font-bold text-green-500">1.82</p>
            </div>
            <div className="text-center p-3 border border-gray-700 rounded">
              <p className="text-sm text-gray-400">Max Drawdown</p>
              <p className="text-xl font-bold text-yellow-500">18.3%</p>
            </div>
            <div className="text-center p-3 border border-gray-700 rounded">
              <p className="text-sm text-gray-400">Win Rate</p>
              <p className="text-xl font-bold text-green-500">73.1%</p>
            </div>
            <div className="text-center p-3 border border-gray-700 rounded">
              <p className="text-sm text-gray-400">Profit Factor</p>
              <p className="text-xl font-bold text-green-500">2.43</p>
            </div>
            <div className="text-center p-3 border border-gray-700 rounded">
              <p className="text-sm text-gray-400">Recovery Factor</p>
              <p className="text-xl font-bold text-green-500">3.18</p>
            </div>
            <div className="text-center p-3 border border-gray-700 rounded">
              <p className="text-sm text-gray-400">Trades</p>
              <p className="text-xl font-bold">2,476</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModelAnalytics;