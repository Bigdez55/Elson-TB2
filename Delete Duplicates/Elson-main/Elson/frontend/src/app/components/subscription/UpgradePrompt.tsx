import React from 'react';
import { Link } from 'react-router-dom';

interface UpgradePromptProps {
  requiredPlan: string;
  feature: string;
  className?: string;
}

/**
 * A component that prompts the user to upgrade their subscription
 * to access a premium feature.
 */
const UpgradePrompt: React.FC<UpgradePromptProps> = ({ 
  requiredPlan, 
  feature,
  className = ''
}) => {
  // Map feature IDs to more user-friendly names
  const featureNames: Record<string, string> = {
    fractional_shares: 'Fractional Share Trading',
    advanced_trading: 'Advanced Trading Tools',
    ai_recommendations: 'AI-Powered Recommendations',
    unlimited_recurring_investments: 'Unlimited Recurring Investments',
    tax_loss_harvesting: 'Tax Loss Harvesting',
    advanced_education: 'Advanced Educational Content',
    market_data_advanced: 'Advanced Market Data',
    high_yield_savings: 'High-Yield Savings Account',
    retirement_accounts: 'Retirement Accounts',
    api_access: 'API Access',
    custodial_accounts: 'Custodial Accounts',
    guardian_approval: 'Guardian Approval Workflow',
    family_challenges: 'Family Challenges',
    educational_games: 'Educational Games',
    multiple_retirement_accounts: 'Multiple Retirement Accounts'
  };

  // Get a user-friendly name for the feature
  const featureName = featureNames[feature] || feature;
  
  // Format the plan name for display
  const planDisplay = requiredPlan.charAt(0).toUpperCase() + requiredPlan.slice(1);

  return (
    <div className={`bg-blue-50 border border-blue-200 rounded-lg p-4 ${className}`}>
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <svg 
            className="h-5 w-5 text-blue-400" 
            xmlns="http://www.w3.org/2000/svg" 
            viewBox="0 0 20 20" 
            fill="currentColor"
          >
            <path 
              fillRule="evenodd" 
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" 
              clipRule="evenodd" 
            />
          </svg>
        </div>
        <div className="ml-3">
          <h3 className="text-sm font-medium text-blue-800">
            Upgrade to access {featureName}
          </h3>
          <div className="mt-2 text-sm text-blue-700">
            <p>
              This feature is available with our {planDisplay} plan.
              Upgrade now to unlock {featureName} and other premium features.
            </p>
          </div>
          <div className="mt-4">
            <Link
              to="/pricing"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              View Plans
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UpgradePrompt;