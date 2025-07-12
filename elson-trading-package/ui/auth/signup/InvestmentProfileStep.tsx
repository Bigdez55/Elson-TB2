import React from 'react';
import { FiBarChart2, FiTarget, FiTrendingUp, FiCpu } from 'react-icons/fi';

// Risk option type for investment profile
type RiskOption = {
  id: string;
  title: string;
  description?: string;
  icon?: React.ReactNode;
};

interface InvestmentProfileStepProps {
  accountType: string;
  investmentGoal: string;
  riskTolerance: string;
  aiManaged: string;
  setAccountType: (value: string) => void;
  setInvestmentGoal: (value: string) => void;
  setRiskTolerance: (value: string) => void;
  setAiManaged: (value: string) => void;
  validationError: string | null;
  validateStep: () => boolean;
}

const InvestmentProfileStep: React.FC<InvestmentProfileStepProps> = ({
  accountType,
  investmentGoal,
  riskTolerance,
  aiManaged,
  setAccountType,
  setInvestmentGoal,
  setRiskTolerance,
  setAiManaged,
  validationError,
}) => {
  // Account type options
  const accountTypeOptions: RiskOption[] = [
    {
      id: 'personal',
      title: 'Personal Account',
      description: 'Invest for yourself with a standard brokerage account',
      icon: <FiTarget className="h-5 w-5 text-purple-400" />
    },
    {
      id: 'custodial',
      title: 'Custodial Account',
      description: 'Invest on behalf of a minor (under 18)',
      icon: <FiTarget className="h-5 w-5 text-purple-400" />
    }
  ];

  // Investment goal options
  const investmentGoalOptions: RiskOption[] = [
    { 
      id: 'retirement', 
      title: 'Saving for retirement',
      icon: <FiTarget className="h-5 w-5 text-purple-400" />
    },
    { 
      id: 'wealth', 
      title: 'Building long-term wealth',
      icon: <FiTrendingUp className="h-5 w-5 text-purple-400" />
    },
    { 
      id: 'major-purchase', 
      title: 'Saving for a major purchase (home, education, etc.)',
      icon: <FiTarget className="h-5 w-5 text-purple-400" />
    },
    { 
      id: 'income', 
      title: 'Generating income',
      icon: <FiBarChart2 className="h-5 w-5 text-purple-400" />
    },
    { 
      id: 'trading', 
      title: 'Short-term trading profits',
      icon: <FiBarChart2 className="h-5 w-5 text-purple-400" />
    }
  ];

  // Risk tolerance options
  const riskToleranceOptions: RiskOption[] = [
    {
      id: 'conservative',
      title: 'Conservative',
      description: 'I want to minimize risk and am willing to accept lower returns',
      icon: <FiBarChart2 className="h-5 w-5 text-blue-400" />
    },
    {
      id: 'moderate',
      title: 'Moderate',
      description: 'I\'m comfortable with some fluctuations to achieve better returns',
      icon: <FiBarChart2 className="h-5 w-5 text-purple-400" />
    },
    {
      id: 'aggressive',
      title: 'Aggressive',
      description: 'I\'m willing to accept significant volatility for potentially higher returns',
      icon: <FiBarChart2 className="h-5 w-5 text-red-400" />
    }
  ];

  // AI Management options
  const aiManagementOptions: RiskOption[] = [
    {
      id: 'ai-managed',
      title: 'Yes, AI-managed',
      description: 'Let our quantum AI build and manage a personalized portfolio for you',
      icon: <FiCpu className="h-5 w-5 text-purple-400" />
    },
    {
      id: 'self-directed',
      title: 'No, self-directed',
      description: 'I prefer to make my own investment decisions (you can change this later)',
      icon: <FiTarget className="h-5 w-5 text-purple-400" />
    }
  ];

  // Function to select a risk option
  const selectOption = (optionType: string, optionId: string) => {
    if (optionType === 'accountType') {
      setAccountType(optionId);
    } else if (optionType === 'investmentGoal') {
      setInvestmentGoal(optionId);
    } else if (optionType === 'riskTolerance') {
      setRiskTolerance(optionId);
    } else if (optionType === 'aiManaged') {
      setAiManaged(optionId);
    }
  };

  // Render option card for investment profile selections
  const renderOptionCard = (optionType: string, option: RiskOption, selectedValue: string) => {
    const isSelected = selectedValue === option.id;
    
    return (
      <div 
        key={option.id}
        className={`border rounded-xl p-5 cursor-pointer transition-all ${
          isSelected ? 'border-purple-600 bg-purple-900 bg-opacity-20' : 'border-gray-700 bg-gray-800 hover:border-purple-600 hover:bg-opacity-10'
        }`}
        onClick={() => selectOption(optionType, option.id)}
      >
        <div className="flex justify-between items-start mb-2">
          <div className="flex items-center">
            {option.icon && <span className="mr-2">{option.icon}</span>}
            <h4 className="text-white font-medium">{option.title}</h4>
          </div>
          {isSelected && (
            <svg className="h-5 w-5 text-purple-400" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"></path>
            </svg>
          )}
        </div>
        {option.description && (
          <p className="text-gray-400 text-sm">{option.description}</p>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-8">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white mb-2">Set your investment profile</h2>
        <p className="text-gray-400">Help us customize your experience based on your investment goals</p>
      </div>

      <div>
        <h3 className="text-lg font-medium text-white mb-4">What type of account would you like to open?</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {accountTypeOptions.map(option => renderOptionCard('accountType', option, accountType))}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-medium text-white mb-4">What is your primary investment goal?</h3>
        <div className="grid grid-cols-1 gap-3">
          {investmentGoalOptions.map(option => renderOptionCard('investmentGoal', option, investmentGoal))}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-medium text-white mb-4">What is your risk tolerance?</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {riskToleranceOptions.map(option => renderOptionCard('riskTolerance', option, riskTolerance))}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-medium text-white mb-4">Would you like our AI to automatically manage your portfolio?</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {aiManagementOptions.map(option => renderOptionCard('aiManaged', option, aiManaged))}
        </div>
      </div>

      {validationError && (
        <div className="text-red-500 text-sm">
          {validationError}
        </div>
      )}
    </div>
  );
};

export default InvestmentProfileStep;