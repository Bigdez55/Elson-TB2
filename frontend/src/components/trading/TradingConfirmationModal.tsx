import React from 'react';
import { useTradingContext } from '../../contexts/TradingContext';
import { formatCurrency } from '../../utils/formatters';
import { calculateFees } from '../../utils/tradingUtils';

interface TradingConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  type: 'order' | 'modeSwitch' | 'risk' | 'general';
  orderDetails?: {
    symbol?: string;
    quantity?: number;
    price?: number;
    action?: 'buy' | 'sell';
    orderType?: string;
  };
}

export const TradingConfirmationModal: React.FC<TradingConfirmationModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  type,
  orderDetails,
}) => {
  const { mode, isBlocked } = useTradingContext();

  if (!isOpen) return null;

  const getModalStyle = () => {
    switch (type) {
      case 'order':
        return mode === 'live' 
          ? 'border-red-500 bg-red-50 border-2' 
          : 'border-yellow-500 bg-yellow-50 border-2';
      case 'modeSwitch':
        return 'border-orange-500 bg-orange-50 border-2';
      case 'risk':
        return 'border-red-600 bg-red-100 border-2';
      default:
        return 'border-gray-300 bg-white border';
    }
  };

  const getButtonStyle = () => {
    switch (type) {
      case 'order':
        return mode === 'live' 
          ? 'bg-red-600 hover:bg-red-700 text-white' 
          : 'bg-yellow-600 hover:bg-yellow-700 text-black';
      case 'modeSwitch':
        return 'bg-orange-600 hover:bg-orange-700 text-white';
      case 'risk':
        return 'bg-red-700 hover:bg-red-800 text-white';
      default:
        return 'bg-blue-600 hover:bg-blue-700 text-white';
    }
  };

  const getIcon = () => {
    switch (type) {
      case 'order':
        return mode === 'live' ? '🚨' : '⚠️';
      case 'modeSwitch':
        return '🔄';
      case 'risk':
        return '⛔';
      default:
        return 'ℹ️';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className={`rounded-lg p-6 max-w-md w-full mx-4 shadow-xl ${getModalStyle()}`}>
        <div className="text-center mb-4">
          <span className="text-4xl">{getIcon()}</span>
        </div>
        
        <h2 className="text-xl font-bold mb-4 text-center text-gray-800">{title}</h2>
        
        {mode === 'live' && type === 'order' && (
          <div className="bg-red-200 border border-red-400 rounded-lg p-3 mb-4">
            <div className="flex items-center justify-center text-red-800 font-medium">
              <span className="text-red-600 mr-2">🔴</span>
              LIVE TRADING MODE ACTIVE
            </div>
            <p className="text-red-700 text-sm text-center mt-1">
              This order will execute with real money
            </p>
          </div>
        )}

        <p className="text-gray-700 mb-4 text-center">{message}</p>

        {orderDetails && (
          <div className="bg-gray-100 rounded-lg p-4 mb-4">
            <h3 className="font-medium text-gray-800 mb-2">Order Details:</h3>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Symbol:</span>
                <span className="font-medium">{orderDetails.symbol}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Action:</span>
                <span className={`font-medium capitalize ${orderDetails.action === 'buy' ? 'text-green-600' : 'text-red-600'}`}>
                  {orderDetails.action}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Quantity:</span>
                <span className="font-medium">{orderDetails.quantity}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Price:</span>
                <span className="font-medium">${orderDetails.price?.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Order Type:</span>
                <span className="font-medium">{orderDetails.orderType}</span>
              </div>
              {orderDetails.quantity && orderDetails.price && (() => {
                const orderValue = orderDetails.quantity * orderDetails.price;
                const fees = calculateFees(orderValue, orderDetails.quantity, mode === 'paper');
                const totalAmount = orderDetails.action === 'buy'
                  ? orderValue + fees.totalFees
                  : orderValue - fees.totalFees;
                return (
                  <>
                    <div className="flex justify-between border-t pt-1 mt-2">
                      <span className="text-gray-600">Subtotal:</span>
                      <span className="font-medium">{formatCurrency(orderValue)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Est. Fees:</span>
                      <span className="font-medium">{formatCurrency(fees.totalFees)}</span>
                    </div>
                    <div className="flex justify-between border-t pt-1 mt-1">
                      <span className="text-gray-600 font-medium">Total {orderDetails.action === 'buy' ? 'Cost' : 'Proceeds'}:</span>
                      <span className={`font-bold ${orderDetails.action === 'buy' ? 'text-red-600' : 'text-green-600'}`}>
                        {formatCurrency(totalAmount)}
                      </span>
                    </div>
                  </>
                );
              })()}
            </div>
          </div>
        )}

        {isBlocked && (
          <div className="bg-red-100 border border-red-300 rounded-lg p-3 mb-4">
            <div className="flex items-center text-red-700">
              <span className="mr-2">🚫</span>
              <span className="font-medium">Trading is currently blocked</span>
            </div>
          </div>
        )}

        {type === 'order' && mode === 'live' && (
          <div className="space-y-2 mb-4">
            <label className="flex items-center text-sm">
              <input type="checkbox" className="mr-2" required />
              I understand this transaction uses real money
            </label>
            <label className="flex items-center text-sm">
              <input type="checkbox" className="mr-2" required />
              I have reviewed the order details above
            </label>
            <label className="flex items-center text-sm">
              <input type="checkbox" className="mr-2" required />
              I am authorized to execute this trade
            </label>
          </div>
        )}

        <div className="flex space-x-3">
          <button
            onClick={onClose}
            className="flex-1 bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg font-medium transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isBlocked}
            className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
              isBlocked 
                ? 'bg-gray-400 text-gray-600 cursor-not-allowed' 
                : getButtonStyle()
            }`}
          >
            {type === 'order' ? 'Execute Order' : 'Confirm'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default TradingConfirmationModal;