import React from 'react';
import Input from '../../common/Input';
import Select from '../../common/Select';
import { FiLock } from 'react-icons/fi';

interface BankConnectionStepProps {
  bankName: string;
  routingNumber: string;
  accountNumber: string;
  accountType: string;
  setBankName: (value: string) => void;
  setRoutingNumber: (value: string) => void;
  setAccountNumber: (value: string) => void;
  setAccountType: (value: string) => void;
  validationError: string | null;
  validateStep: () => boolean;
}

const BankConnectionStep: React.FC<BankConnectionStepProps> = ({
  bankName,
  routingNumber,
  accountNumber,
  accountType,
  setBankName,
  setRoutingNumber,
  setAccountNumber,
  setAccountType,
  validationError,
}) => {
  // Bank options 
  const bankOptions = [
    { name: 'Chase', logo: '🏦' },
    { name: 'Bank of America', logo: '🏦' },
    { name: 'Wells Fargo', logo: '🏦' },
    { name: 'Citibank', logo: '🏦' },
    { name: 'Capital One', logo: '🏦' },
    { name: 'Other Bank', logo: '➕' }
  ];

  return (
    <div className="space-y-6">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white mb-2">Connect your bank account</h2>
        <p className="text-gray-400">Securely link your bank to fund your investments</p>
      </div>

      <div className="bg-gray-800 rounded-xl p-6 mb-8">
        <div className="flex items-start">
          <div className="h-10 w-10 bg-purple-900 rounded-full flex items-center justify-center flex-shrink-0">
            <FiLock className="h-5 w-5 text-purple-300" />
          </div>
          <div className="ml-4">
            <h3 className="text-white font-medium mb-1">Bank-level Security</h3>
            <p className="text-gray-400 text-sm">Elson uses 256-bit encryption and never stores your banking credentials. We use Plaid to securely connect to your bank.</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        {bankOptions.map(bank => (
          <div 
            key={bank.name}
            className={`bg-gray-800 p-4 rounded-xl flex flex-col items-center justify-center cursor-pointer hover:bg-gray-700 transition-colors ${
              bankName === bank.name ? 'border-2 border-purple-500' : ''
            }`}
            onClick={() => setBankName(bank.name)}
          >
            <div className="text-3xl mb-2">{bank.logo}</div>
            <span className="text-sm text-gray-300">{bank.name}</span>
          </div>
        ))}
      </div>

      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 mt-6">
        <h4 className="text-white font-medium mb-2">Manual Account Setup</h4>
        <p className="text-gray-400 text-sm mb-4">Prefer to set up manually? Enter your account details below.</p>

        <div className="space-y-4">
          <Input
            label="Bank Name"
            type="text"
            value={bankName}
            onChange={(e) => setBankName(e.target.value)}
            placeholder="Enter your bank name"
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Routing Number"
              type="text"
              value={routingNumber}
              onChange={(e) => setRoutingNumber(e.target.value)}
              placeholder="000000000"
            />
            <Input
              label="Account Number"
              type="text"
              value={accountNumber}
              onChange={(e) => setAccountNumber(e.target.value)}
              placeholder="00000000000"
            />
          </div>

          <Select
            label="Account Type"
            value={accountType}
            onChange={(value) => setAccountType(value)}
            options={[
              { value: 'checking', label: 'Checking' },
              { value: 'savings', label: 'Savings' }
            ]}
            placeholder="Select account type"
          />
        </div>
      </div>

      {validationError && (
        <div className="text-red-500 text-sm">
          {validationError}
        </div>
      )}
      
      <div className="mt-4 bg-purple-900 bg-opacity-20 rounded-lg p-4 border border-purple-800">
        <p className="text-purple-400 text-sm flex items-start">
          <FiLock className="h-5 w-5 mr-2 flex-shrink-0 mt-0.5" />
          <span>You can also complete this step later. If you prefer to explore the platform first, you can add a bank account when you&apos;re ready to make your first investment.</span>
        </p>
      </div>
    </div>
  );
};

export default BankConnectionStep;