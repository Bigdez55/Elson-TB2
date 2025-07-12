import React from 'react';

const TradingPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Manual Trading</h1>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Place Order</h3>
        <p className="text-gray-600">
          Manual trading functionality will be implemented here. This includes:
        </p>
        <ul className="mt-2 text-gray-600 list-disc list-inside">
          <li>Stock symbol search and validation</li>
          <li>Real-time price quotes</li>
          <li>Order placement (market, limit, stop orders)</li>
          <li>Order history and tracking</li>
          <li>Position management</li>
        </ul>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-medium text-blue-800 mb-2">💡 Try Advanced Trading</h3>
        <p className="text-blue-700">
          For AI-powered trading strategies and automated execution, check out our 
          <a href="/advanced-trading" className="font-medium underline ml-1">Advanced Trading</a> features.
        </p>
      </div>
    </div>
  );
};

export default TradingPage;