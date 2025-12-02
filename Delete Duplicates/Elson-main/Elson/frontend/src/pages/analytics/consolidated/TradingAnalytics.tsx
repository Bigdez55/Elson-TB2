import React from 'react';

/**
 * Consolidated Trading Analytics component that combines:
 * - Trading Analytics
 * - Trading Bot Analytics
 * - Trading Pair Analytics
 * - Order Book Analytics
 */
const TradingAnalytics: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Trading Analytics</h1>
      </div>

      {/* Trading overview stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-gray-400 text-sm">Total Trades</h3>
          <p className="text-2xl font-bold mt-1">356</p>
          <p className="text-sm text-gray-400">+42 this month</p>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-gray-400 text-sm">Win Rate</h3>
          <p className="text-2xl font-bold mt-1 text-green-500">68.4%</p>
          <p className="text-sm text-gray-400">+2.7% improvement</p>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-gray-400 text-sm">Average Profit</h3>
          <p className="text-2xl font-bold mt-1">$87.32</p>
          <p className="text-sm text-gray-400">per winning trade</p>
        </div>
      </div>

      {/* Trading Bots Performance */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h2 className="text-xl font-semibold mb-4">Trading Bot Performance</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="border border-gray-700 rounded p-4">
            <h3 className="font-medium text-lg mb-2">Momentum Bot</h3>
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm text-gray-400">Win Rate</p>
                <p className="text-green-500 font-medium">72.3%</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Profit</p>
                <p className="text-green-500 font-medium">$3,482.76</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Trades</p>
                <p>128</p>
              </div>
            </div>
          </div>
          <div className="border border-gray-700 rounded p-4">
            <h3 className="font-medium text-lg mb-2">Mean Reversion Bot</h3>
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm text-gray-400">Win Rate</p>
                <p className="text-green-500 font-medium">64.7%</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Profit</p>
                <p className="text-green-500 font-medium">$2,156.43</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Trades</p>
                <p>98</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Trading Pair Performance */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h2 className="text-xl font-semibold mb-4">Top Trading Pairs</h2>
        <table className="min-w-full">
          <thead>
            <tr className="border-b border-gray-700">
              <th className="text-left pb-2">Pair</th>
              <th className="text-left pb-2">Win Rate</th>
              <th className="text-left pb-2">Profit/Loss</th>
              <th className="text-left pb-2">Volume</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td className="py-2">AAPL/USD</td>
              <td className="py-2 text-green-500">75.3%</td>
              <td className="py-2 text-green-500">$1,532.87</td>
              <td className="py-2">$24,356.78</td>
            </tr>
            <tr>
              <td className="py-2">MSFT/USD</td>
              <td className="py-2 text-green-500">68.9%</td>
              <td className="py-2 text-green-500">$982.34</td>
              <td className="py-2">$18,945.32</td>
            </tr>
            <tr>
              <td className="py-2">AMZN/USD</td>
              <td className="py-2 text-green-500">62.1%</td>
              <td className="py-2 text-green-500">$764.55</td>
              <td className="py-2">$15,678.91</td>
            </tr>
            <tr>
              <td className="py-2">TSLA/USD</td>
              <td className="py-2 text-yellow-500">54.8%</td>
              <td className="py-2 text-red-500">-$123.45</td>
              <td className="py-2">$9,876.54</td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Order Book Analysis */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h2 className="text-xl font-semibold mb-4">Order Book Analysis</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-medium mb-2">Market Depth</h3>
            <p className="text-sm text-gray-400 mb-4">
              Visualization shows buy/sell pressure across price levels
            </p>
            <div className="h-48 bg-gray-700 rounded flex items-center justify-center">
              [Market Depth Chart Placeholder]
            </div>
          </div>
          <div>
            <h3 className="text-lg font-medium mb-2">Order Flow</h3>
            <p className="text-sm text-gray-400 mb-4">
              Tracks order volume and direction over time
            </p>
            <div className="h-48 bg-gray-700 rounded flex items-center justify-center">
              [Order Flow Chart Placeholder]
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TradingAnalytics;