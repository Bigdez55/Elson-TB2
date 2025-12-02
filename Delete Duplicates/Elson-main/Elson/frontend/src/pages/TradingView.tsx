import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useTrading } from '../hooks/useTrading';
import { useWebSocket } from '../hooks/useWebSocket';
import CandlestickChart from '../components/charts/CandlestickChart';
import VolumeChart from '../components/charts/VolumeChart';
import IndicatorChart from '../components/charts/IndicatorChart';
import OrderForm from '../components/trading/OrderForm';
import TradeHistory from '../components/trading/TradeHistory';
import OrderBook from '../components/trading/OrderBook';
import MarketDepth from '../components/trading/MarketDepth';
import Select from '../components/common/Select';
import Loading from '../components/common/Loading';
import { formatCurrency, formatPercentage } from '../utils/formatters';

export default function TradingView() {
  const [symbol, setSymbol] = useState('BTC/USD');
  const [timeframe, setTimeframe] = useState('1h');
  const { marketData, orderBook, trades, loading } = useTrading(symbol);
  
  useWebSocket(['market', 'trades', 'orders'], { symbol });

  const [chartLayout, setChartLayout] = useState('default');
  const [selectedIndicators, setSelectedIndicators] = useState(['RSI', 'MACD']);

  if (loading) return <Loading />;

  return (
    <div className="h-full flex flex-col">
      {/* Trading Header */}
      <div className="bg-gray-800 p-4 border-b border-gray-700">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <Select
              value={symbol}
              onChange={setSymbol}
              options={[
                { value: 'BTC/USD', label: 'Bitcoin/USD' },
                { value: 'ETH/USD', label: 'Ethereum/USD' },
                { value: 'SOL/USD', label: 'Solana/USD' },
              ]}
              className="w-40"
            />
            <Select
              value={timeframe}
              onChange={setTimeframe}
              options={[
                { value: '1m', label: '1 Minute' },
                { value: '5m', label: '5 Minutes' },
                { value: '1h', label: '1 Hour' },
                { value: '1d', label: '1 Day' },
              ]}
              className="w-32"
            />
          </div>

          <div className="flex items-center space-x-6">
            <div>
              <span className="text-gray-400">Last Price</span>
              <div className={`text-lg font-semibold ${
                marketData?.priceChange24h >= 0 ? 'text-green-500' : 'text-red-500'
              }`}>
                {formatCurrency(marketData?.price)}
              </div>
            </div>
            <div>
              <span className="text-gray-400">24h Change</span>
              <div className={`text-lg font-semibold ${
                marketData?.priceChange24h >= 0 ? 'text-green-500' : 'text-red-500'
              }`}>
                {formatPercentage(marketData?.priceChange24h)}
              </div>
            </div>
            <div>
              <span className="text-gray-400">24h Volume</span>
              <div className="text-lg font-semibold">
                {formatCurrency(marketData?.volume24h)}
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <Select
              value={chartLayout}
              onChange={setChartLayout}
              options={[
                { value: 'default', label: 'Default Layout' },
                { value: 'advanced', label: 'Advanced' },
                { value: 'compact', label: 'Compact' },
              ]}
              className="w-40"
            />
          </div>
        </div>
      </div>

      {/* Main Trading Area */}
      <div className="flex-1 grid grid-cols-4 gap-4 p-4">
        {/* Charts Section */}
        <div className="col-span-3 space-y-4">
          <div className="bg-gray-800 p-4 rounded-lg">
            <CandlestickChart
              data={marketData?.candles || []}
              height={500}
              timeframe={timeframe}
            />
          </div>

          <div className="bg-gray-800 p-4 rounded-lg">
            <VolumeChart
              data={marketData?.volume || []}
              height={150}
            />
          </div>

          {selectedIndicators.includes('RSI') && (
            <div className="bg-gray-800 p-4 rounded-lg">
              <IndicatorChart
                type="RSI"
                data={marketData?.indicators?.rsi || []}
                height={150}
              />
            </div>
          )}

          {selectedIndicators.includes('MACD') && (
            <div className="bg-gray-800 p-4 rounded-lg">
              <IndicatorChart
                type="MACD"
                data={marketData?.indicators?.macd || []}
                height={150}
              />
            </div>
          )}
        </div>

        {/* Trading Panel */}
        <div className="space-y-4">
          <div className="bg-gray-800 p-4 rounded-lg">
            <OrderForm
              symbol={symbol}
              currentPrice={marketData?.price}
            />
          </div>

          <div className="bg-gray-800 p-4 rounded-lg">
            <OrderBook
              data={orderBook}
              depth={10}
            />
          </div>

          <div className="bg-gray-800 p-4 rounded-lg">
            <MarketDepth
              data={orderBook}
              height={200}
            />
          </div>
        </div>
      </div>

      {/* Trade History */}
      <div className="h-64 bg-gray-800 border-t border-gray-700">
        <TradeHistory
          symbol={symbol}
          trades={trades}
        />
      </div>
    </div>
  );
}