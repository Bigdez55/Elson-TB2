import React from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../store/store';
import AdvancedTradingDashboard from '../components/AdvancedTrading/AdvancedTradingDashboard';

const AdvancedTradingPage: React.FC = () => {
  const { portfolio } = useSelector((state: RootState) => state.portfolio);

  // Default portfolio ID - in a real app, this would come from the selected portfolio
  const portfolioId = portfolio?.id || 1;

  return (
    <div className="min-h-screen bg-gray-50">
      <AdvancedTradingDashboard portfolioId={portfolioId} />
    </div>
  );
};

export default AdvancedTradingPage;