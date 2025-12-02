import React from 'react';

/**
 * Consolidated Market Analytics component that combines:
 * - Market Analytics
 * - Exchange Analytics
 * - Data Analytics
 * - Event Analytics
 */
const MarketAnalytics: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Market Analytics</h1>
      </div>

      {/* Market overview stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-gray-400 text-sm">Market Regime</h3>
          <p className="text-2xl font-bold mt-1 text-yellow-500">Medium Volatility</p>
          <p className="text-sm text-gray-400">Transitioned 3 days ago</p>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-gray-400 text-sm">VIX Index</h3>
          <p className="text-2xl font-bold mt-1">24.36</p>
          <p className="text-sm text-gray-400">+2.14 (9.6%)</p>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-gray-400 text-sm">Market Breadth</h3>
          <p className="text-2xl font-bold mt-1 text-red-500">-0.32</p>
          <p className="text-sm text-gray-400">Bearish trend forming</p>
        </div>
      </div>

      {/* Market Breadth Analysis */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h2 className="text-xl font-semibold mb-4">Market Breadth Analysis</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-medium mb-2">Advance-Decline Line</h3>
            <div className="h-48 bg-gray-700 rounded-lg flex items-center justify-center">
              [AD Line Chart Placeholder]
            </div>
          </div>
          <div>
            <h3 className="text-lg font-medium mb-2">Up-Down Volume Ratio</h3>
            <div className="h-48 bg-gray-700 rounded-lg flex items-center justify-center">
              [Volume Ratio Chart Placeholder]
            </div>
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <div className="text-center p-3 border border-gray-700 rounded">
            <p className="text-sm text-gray-400">Advancing Issues</p>
            <p className="text-xl font-bold text-red-500">1,245</p>
          </div>
          <div className="text-center p-3 border border-gray-700 rounded">
            <p className="text-sm text-gray-400">Declining Issues</p>
            <p className="text-xl font-bold text-green-500">1,872</p>
          </div>
          <div className="text-center p-3 border border-gray-700 rounded">
            <p className="text-sm text-gray-400">New Highs</p>
            <p className="text-xl font-bold text-green-500">78</p>
          </div>
          <div className="text-center p-3 border border-gray-700 rounded">
            <p className="text-sm text-gray-400">New Lows</p>
            <p className="text-xl font-bold text-red-500">132</p>
          </div>
        </div>
      </div>

      {/* Sector Rotation Analysis */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h2 className="text-xl font-semibold mb-4">Sector Rotation Analysis</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left pb-2">Sector</th>
                <th className="text-left pb-2">1-Day</th>
                <th className="text-left pb-2">1-Week</th>
                <th className="text-left pb-2">1-Month</th>
                <th className="text-left pb-2">3-Month</th>
                <th className="text-left pb-2">Relative Strength</th>
                <th className="text-left pb-2">Money Flow</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-gray-700">
                <td className="py-3">
                  <div className="font-medium">Technology</div>
                </td>
                <td className="py-3 text-red-500">-0.82%</td>
                <td className="py-3 text-green-500">1.47%</td>
                <td className="py-3 text-green-500">4.32%</td>
                <td className="py-3 text-green-500">12.87%</td>
                <td className="py-3">
                  <div className="h-2 w-32 bg-gray-700 rounded">
                    <div className="h-2 bg-green-500 rounded" style={{ width: '85%' }}></div>
                  </div>
                </td>
                <td className="py-3 text-green-500">Strong Inflow</td>
              </tr>
              <tr className="border-b border-gray-700">
                <td className="py-3">
                  <div className="font-medium">Healthcare</div>
                </td>
                <td className="py-3 text-green-500">0.45%</td>
                <td className="py-3 text-green-500">2.12%</td>
                <td className="py-3 text-green-500">3.87%</td>
                <td className="py-3 text-green-500">8.43%</td>
                <td className="py-3">
                  <div className="h-2 w-32 bg-gray-700 rounded">
                    <div className="h-2 bg-green-500 rounded" style={{ width: '72%' }}></div>
                  </div>
                </td>
                <td className="py-3 text-green-500">Moderate Inflow</td>
              </tr>
              <tr className="border-b border-gray-700">
                <td className="py-3">
                  <div className="font-medium">Financials</div>
                </td>
                <td className="py-3 text-red-500">-1.23%</td>
                <td className="py-3 text-red-500">-2.84%</td>
                <td className="py-3 text-green-500">1.42%</td>
                <td className="py-3 text-green-500">5.78%</td>
                <td className="py-3">
                  <div className="h-2 w-32 bg-gray-700 rounded">
                    <div className="h-2 bg-yellow-500 rounded" style={{ width: '58%' }}></div>
                  </div>
                </td>
                <td className="py-3 text-yellow-500">Neutral</td>
              </tr>
              <tr className="border-b border-gray-700">
                <td className="py-3">
                  <div className="font-medium">Energy</div>
                </td>
                <td className="py-3 text-red-500">-2.87%</td>
                <td className="py-3 text-red-500">-4.32%</td>
                <td className="py-3 text-red-500">-6.78%</td>
                <td className="py-3 text-red-500">-12.45%</td>
                <td className="py-3">
                  <div className="h-2 w-32 bg-gray-700 rounded">
                    <div className="h-2 bg-red-500 rounded" style={{ width: '27%' }}></div>
                  </div>
                </td>
                <td className="py-3 text-red-500">Strong Outflow</td>
              </tr>
              <tr>
                <td className="py-3">
                  <div className="font-medium">Utilities</div>
                </td>
                <td className="py-3 text-green-500">0.87%</td>
                <td className="py-3 text-green-500">1.32%</td>
                <td className="py-3 text-green-500">2.45%</td>
                <td className="py-3 text-red-500">-1.24%</td>
                <td className="py-3">
                  <div className="h-2 w-32 bg-gray-700 rounded">
                    <div className="h-2 bg-yellow-500 rounded" style={{ width: '50%' }}></div>
                  </div>
                </td>
                <td className="py-3 text-yellow-500">Neutral</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Market Event Analysis */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h2 className="text-xl font-semibold mb-4">Market Event Analysis</h2>
        <div className="space-y-4">
          <div className="border border-gray-700 rounded-lg p-4">
            <div className="flex justify-between items-center">
              <div>
                <div className="font-medium text-lg">FOMC Meeting</div>
                <div className="text-sm text-gray-400">Next: May 1, 2025</div>
              </div>
              <div className="px-3 py-1 bg-yellow-800 text-yellow-300 rounded-full text-sm">High Impact</div>
            </div>
            <div className="mt-3">
              <div className="text-sm">Historical market reaction:</div>
              <div className="grid grid-cols-3 gap-4 mt-2">
                <div>
                  <div className="text-sm text-gray-400">SPY Average Move</div>
                  <div className="text-lg">±1.42%</div>
                </div>
                <div>
                  <div className="text-sm text-gray-400">VIX Average Change</div>
                  <div className="text-lg">+2.7 points</div>
                </div>
                <div>
                  <div className="text-sm text-gray-400">Direction Bias</div>
                  <div className="text-lg text-green-500">65% Bullish</div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="border border-gray-700 rounded-lg p-4">
            <div className="flex justify-between items-center">
              <div>
                <div className="font-medium text-lg">Earnings Season</div>
                <div className="text-sm text-gray-400">Current: Q1 2025</div>
              </div>
              <div className="px-3 py-1 bg-yellow-800 text-yellow-300 rounded-full text-sm">High Impact</div>
            </div>
            <div className="mt-3">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <div className="text-sm text-gray-400">Companies Reported</div>
                  <div className="text-lg">342 / 500 S&P 500</div>
                </div>
                <div>
                  <div className="text-sm text-gray-400">Beat Expectations</div>
                  <div className="text-lg text-green-500">67%</div>
                </div>
                <div>
                  <div className="text-sm text-gray-400">Missed Expectations</div>
                  <div className="text-lg text-red-500">24%</div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="border border-gray-700 rounded-lg p-4">
            <div className="flex justify-between items-center">
              <div>
                <div className="font-medium text-lg">Economic Calendar</div>
                <div className="text-sm text-gray-400">Upcoming 7 days</div>
              </div>
            </div>
            <div className="mt-3 space-y-2">
              <div className="flex justify-between items-center pb-2 border-b border-gray-700">
                <div className="text-sm">Apr 22 - Retail Sales</div>
                <div className="px-2 py-0.5 bg-yellow-800 text-yellow-300 rounded text-xs">Medium</div>
              </div>
              <div className="flex justify-between items-center pb-2 border-b border-gray-700">
                <div className="text-sm">Apr 23 - Existing Home Sales</div>
                <div className="px-2 py-0.5 bg-green-800 text-green-300 rounded text-xs">Low</div>
              </div>
              <div className="flex justify-between items-center pb-2 border-b border-gray-700">
                <div className="text-sm">Apr 24 - Initial Jobless Claims</div>
                <div className="px-2 py-0.5 bg-yellow-800 text-yellow-300 rounded text-xs">Medium</div>
              </div>
              <div className="flex justify-between items-center">
                <div className="text-sm">Apr 26 - GDP (Advance)</div>
                <div className="px-2 py-0.5 bg-red-800 text-red-300 rounded text-xs">High</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MarketAnalytics;