import React from 'react';
import WebSocketTest from '../app/components/trading/WebSocketTest';

const WebSocketTestPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-100 py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow-lg rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h1 className="text-3xl font-bold text-center mb-8 text-gray-800">
              WebSocket Test Page
            </h1>
            <WebSocketTest />
          </div>
        </div>
      </div>
    </div>
  );
};

export default WebSocketTestPage;