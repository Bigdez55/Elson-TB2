import React, { useState, useEffect } from 'react';
import { useMarketWebSocket } from '../../hooks/useMarketWebSocket';

const WebSocketTest: React.FC = () => {
  const [symbols, setSymbols] = useState<string[]>(['AAPL', 'MSFT', 'GOOGL']);
  const [newSymbol, setNewSymbol] = useState('');

  // Connect to WebSocket
  const { isConnected, error, quotes, subscribe, unsubscribe, reconnect } = useMarketWebSocket({
    autoConnect: true
  });

  // Subscribe to initial symbols when connected
  useEffect(() => {
    if (isConnected && symbols.length > 0) {
      subscribe(symbols);
    }
  }, [isConnected, subscribe]); // Only run when connection status changes
  
  // Function to add a new symbol
  const handleAddSymbol = () => {
    if (!newSymbol) return;
    
    const symbol = newSymbol.trim().toUpperCase();
    if (!symbols.includes(symbol)) {
      const newSymbols = [...symbols, symbol];
      setSymbols(newSymbols);
      subscribe([symbol]);
    }
    
    setNewSymbol('');
  };
  
  // Function to remove a symbol
  const handleRemoveSymbol = (symbol: string) => {
    const newSymbols = symbols.filter(s => s !== symbol);
    setSymbols(newSymbols);
    unsubscribe([symbol]);
  };
  
  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">WebSocket Test</h1>
      
      {/* Connection status */}
      <div className="mb-4 flex items-center">
        <div className={`w-3 h-3 rounded-full mr-2 ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
        <span className={isConnected ? 'text-green-600' : 'text-red-600'}>
          {isConnected ? 'Connected' : 'Disconnected'}
        </span>
        <button 
          onClick={reconnect}
          className="ml-4 px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
        >
          Reconnect
        </button>
      </div>
      
      {/* Error display */}
      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-300 text-red-600 rounded">
          {error}
        </div>
      )}
      
      {/* Add symbol form */}
      <div className="mb-6 flex">
        <input
          type="text"
          value={newSymbol}
          onChange={(e) => setNewSymbol(e.target.value)}
          placeholder="Enter symbol (e.g., AAPL)"
          className="flex-1 px-4 py-2 border border-gray-300 rounded-l focus:outline-none focus:ring-2 focus:ring-blue-600"
        />
        <button
          onClick={handleAddSymbol}
          className="px-4 py-2 bg-blue-600 text-white rounded-r hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-600"
        >
          Add Symbol
        </button>
      </div>
      
      {/* Subscribed symbols */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold mb-2">Subscribed Symbols</h2>
        <div className="flex flex-wrap gap-2">
          {symbols.map(symbol => (
            <div 
              key={symbol} 
              className="px-3 py-1 bg-gray-200 rounded-full flex items-center"
            >
              <span>{symbol}</span>
              <button 
                onClick={() => handleRemoveSymbol(symbol)}
                className="ml-2 w-5 h-5 rounded-full bg-gray-400 text-white flex items-center justify-center hover:bg-gray-500"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      </div>
      
      {/* Market data display */}
      <div>
        <h2 className="text-lg font-semibold mb-2">Real-time Market Data</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.values(quotes).map(quote => (
            <div 
              key={quote.symbol}
              className="p-4 border border-gray-300 rounded shadow-sm"
            >
              <div className="flex justify-between items-center mb-2">
                <h3 className="text-xl font-bold">{quote.symbol}</h3>
                <span className="text-xl font-semibold">${quote.price.toFixed(2)}</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-gray-500">Bid:</span>
                  <span className="ml-2">${quote.bid?.toFixed(2) || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-gray-500">Ask:</span>
                  <span className="ml-2">${quote.ask?.toFixed(2) || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-gray-500">Volume:</span>
                  <span className="ml-2">{quote.volume?.toLocaleString() || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-gray-500">Updated:</span>
                  <span className="ml-2">{new Date(quote.timestamp).toLocaleTimeString()}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        {Object.keys(quotes).length === 0 && (
          <div className="p-8 text-center text-gray-500 border border-dashed border-gray-300 rounded">
            No market data available. Subscribe to symbols to see real-time quotes.
          </div>
        )}
      </div>
    </div>
  );
};

export default WebSocketTest;