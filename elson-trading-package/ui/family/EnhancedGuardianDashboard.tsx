import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { formatCurrency, formatPercentage } from '../../utils/formatters';
import api from '../../services/api';

// Chart import
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Filler, Legend } from 'chart.js';
import { Line } from 'react-chartjs-2';
import { useSubscription } from '../../hooks/useSubscription';
import { SubscriptionPlan } from '../../services/subscriptionService';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
  Legend
);

// Define types
interface FamilyMember {
  id: string;
  initials: string;
  name: string;
  role: string;
  age?: string;
  status: 'online' | 'away' | 'offline';
  color: string;
}

interface AccountBreakdown {
  member: FamilyMember;
  balance: number;
  percentage: number;
}

interface Minor {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  birthdate: string;
  guardian_id: number;
  guardian_name: string;
  account_id: number;
}

interface PendingTrade {
  trade_id: number;
  minor_id: number;
  minor_name: string;
  symbol: string;
  quantity: number;
  price: number;
  trade_type: string;
  status: string;
  created_at: string;
  approved_at?: string;
  rejection_reason?: string;
}

interface GuardianStatus {
  is_guardian: boolean;
  minor_count: number;
  total_trades: number;
  pending_approvals: number;
  two_factor_enabled: boolean;
  requires_2fa_setup: boolean;
}

interface LearningProgress {
  member: FamilyMember;
  progress: number;
  course: string;
  lessons: {
    completed: number;
    total: number;
  };
}

interface Badge {
  id: string;
  name: string;
  earned: boolean;
  icon: string;
  color: string;
}

interface FamilyChallenge {
  title: string;
  description: string;
  timeLeft: string;
  leader: {
    name: string;
    performance: string;
  };
  participants: {
    member: FamilyMember;
    symbol: string;
    performance: string;
    progress: number;
    status: 'gold' | 'silver' | 'normal';
  }[];
}

interface EducationalEvent {
  date: string;
  title: string;
  description: string;
}

const colorOptions = ['purple', 'blue', 'green', 'pink', 'yellow', 'red', 'indigo'];

// Static data for components that don't have API endpoints yet
const educationalEvents: EducationalEvent[] = [
  {
    date: '15 AUG',
    title: 'Investing for College',
    description: 'Interactive webinar for teens about long-term education planning'
  },
  {
    date: '22 AUG',
    title: 'Stock Market Basics',
    description: 'Kid-friendly introduction to how stocks work'
  }
];

const badges: Badge[] = [
  {
    id: 'badge-01',
    name: 'First Trade',
    earned: true,
    icon: 'lightbulb',
    color: 'purple'
  },
  {
    id: 'badge-02',
    name: 'Diversifier',
    earned: true,
    icon: 'shield',
    color: 'blue'
  },
  {
    id: 'badge-03',
    name: 'Growth Expert',
    earned: false,
    icon: 'trending-up',
    color: 'gray'
  }
];

const EnhancedGuardianDashboard: React.FC = () => {
  // State
  const [currentTab, setCurrentTab] = useState<'overview' | 'approval-requests' | 'educational-center' | 'settings'>('overview');
  const [familyPortfolioTimeframe, setFamilyPortfolioTimeframe] = useState<'all' | 'year' | 'month'>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [guardian, setGuardian] = useState<FamilyMember | null>(null);
  const [familyMembers, setFamilyMembers] = useState<FamilyMember[]>([]);
  const [minors, setMinors] = useState<Minor[]>([]);
  const [pendingTrades, setPendingTrades] = useState<PendingTrade[]>([]);
  const [guardianStatus, setGuardianStatus] = useState<GuardianStatus | null>(null);
  const [accountBreakdowns, setAccountBreakdowns] = useState<AccountBreakdown[]>([]);
  const [portfolioValue, setPortfolioValue] = useState(0);
  const [portfolioGrowth, setPortfolioGrowth] = useState(0);
  const [showAddModal, setShowAddModal] = useState(false);
  
  const navigate = useNavigate();
  const { subscription, isLoading: isSubscriptionLoading } = useSubscription();
  
  // Initialize chart.js reference
  const chartRef = useRef<ChartJS>(null);

  // Chart data for family portfolio
  const [portfolioChartData, setPortfolioChartData] = useState({
    labels: Array.from({length: 30}, (_, i) => i + 1), // Last 30 days
    datasets: [{
      label: 'Family Portfolio Value',
      data: [
        42000, 42300, 41800, 42500, 43100, 43500, 43800, 44200, 44000, 43700,
        44500, 45100, 45800, 46200, 46000, 45700, 46500, 46800, 46300, 47000,
        47500, 48100, 47800, 47500, 47900, 48300, 48600, 48200, 48800, 49200
      ],
      borderColor: 'rgba(139, 92, 246, 1)',
      backgroundColor: 'rgba(139, 92, 246, 0.1)',
      borderWidth: 2,
      pointRadius: 0,
      pointHoverRadius: 5,
      tension: 0.3,
      fill: true
    }]
  });

  // Check if user is on family plan
  const hasFamilyPlan = !isSubscriptionLoading && subscription && subscription.plan === SubscriptionPlan.FAMILY;

  // Fetch data from API
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        // Get user info to create guardian object
        const userResponse = await api.get('/api/v1/users/me');
        const user = userResponse.data;
        
        setGuardian({
          id: `g-${user.id}`,
          initials: getInitials(user.first_name, user.last_name),
          name: `${user.first_name} ${user.last_name}`,
          role: 'Guardian',
          status: 'online',
          color: colorOptions[0]
        });
        
        // Get guardian status
        const statusResponse = await api.get('/api/v1/family/guardian/status');
        setGuardianStatus(statusResponse.data);
        
        // Get minors under guardianship
        const minorsResponse = await api.get('/api/v1/family/minors');
        setMinors(minorsResponse.data);
        
        // Convert minors to family members format for UI
        const familyMembersList = minorsResponse.data.map((minor: Minor, index: number) => ({
          id: `f-${minor.id}`,
          initials: getInitials(minor.first_name, minor.last_name),
          name: `${minor.first_name} ${minor.last_name}`,
          role: calculateAge(minor.birthdate) + ' years old',
          status: 'online',
          color: colorOptions[(index % colorOptions.length) + 1]
        }));
        
        setFamilyMembers(familyMembersList);
        
        // Get pending trades
        const tradesResponse = await api.get('/api/v1/family/trades/pending');
        setPendingTrades(tradesResponse.data);
        
        // Get portfolio data for each family member
        // This would normally be an API call like:
        // const portfolioResponse = await api.get('/api/v1/family/portfolio');
        // But for now we'll generate mock data based on the family members
        
        const portfolioData = await generatePortfolioData(user, familyMembersList);
        setAccountBreakdowns(portfolioData.breakdowns);
        setPortfolioValue(portfolioData.totalValue);
        setPortfolioGrowth(portfolioData.growth);
        
      } catch (err: any) {
        console.error('Error fetching guardian data:', err);
        setError(err.message || 'Failed to load family data');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchData();
  }, []);

  // Helper functions
  const getInitials = (firstName: string, lastName: string): string => {
    return `${firstName.charAt(0)}${lastName.charAt(0)}`;
  };
  
  const calculateAge = (birthdate: string): number => {
    const today = new Date();
    const birth = new Date(birthdate);
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
      age--;
    }
    
    return age;
  };
  
  const generatePortfolioData = async (guardian: any, familyMembers: FamilyMember[]) => {
    // Mock data generation - in a real app this would come from the API
    const guardianBalance = 34567.89;
    const totalValue = guardianBalance + familyMembers.reduce((sum, _, index) => {
      // Generate a random balance between $1000 and $10000 for each family member
      return sum + (1000 + Math.random() * 9000);
    }, 0);
    
    const guardianPercentage = Math.round((guardianBalance / totalValue) * 100);
    const remainingPercentage = 100 - guardianPercentage;
    
    // Distribute the remaining percentage among family members
    const percentages = [];
    let remaining = remainingPercentage;
    
    for (let i = 0; i < familyMembers.length - 1; i++) {
      // Allocate a percentage between 5% and remaining/2
      const max = Math.min(30, remaining / 2);
      const min = Math.min(5, remaining);
      const percentage = Math.floor(min + Math.random() * (max - min));
      percentages.push(percentage);
      remaining -= percentage;
    }
    
    // Last member gets the remaining percentage
    percentages.push(remaining);
    
    // Create account breakdowns
    const breakdowns: AccountBreakdown[] = [{
      member: {
        id: guardian.id,
        initials: getInitials(guardian.first_name, guardian.last_name),
        name: `${guardian.first_name} ${guardian.last_name}`,
        role: 'Guardian',
        status: 'online',
        color: 'purple'
      },
      balance: guardianBalance,
      percentage: guardianPercentage
    }];
    
    familyMembers.forEach((member, index) => {
      const percentage = percentages[index] || 0;
      const balance = (percentage / 100) * totalValue;
      
      breakdowns.push({
        member,
        balance,
        percentage
      });
    });
    
    return {
      breakdowns,
      totalValue,
      growth: 14.2 // Mock growth percentage
    };
  };

  // Handlers
  const handleTabChange = (tab: 'overview' | 'approval-requests' | 'educational-center' | 'settings') => {
    setCurrentTab(tab);
  };

  const handleApproveRequest = async (tradeId: number) => {
    try {
      await api.post(`/api/v1/family/trade/${tradeId}/approve`, {
        approved: true
      });
      
      // Update the UI to remove the approved trade
      setPendingTrades(pendingTrades.filter(trade => trade.trade_id !== tradeId));
      
      // Refresh guardian status to update counts
      const statusResponse = await api.get('/api/v1/family/guardian/status');
      setGuardianStatus(statusResponse.data);
    } catch (err: any) {
      console.error('Error approving trade:', err);
      alert('Failed to approve trade: ' + (err.message || 'Unknown error'));
    }
  };

  const handleDenyRequest = async (tradeId: number) => {
    try {
      const reason = prompt('Please provide a reason for denying this trade:');
      
      await api.post(`/api/v1/family/trade/${tradeId}/approve`, {
        approved: false,
        rejection_reason: reason || 'Denied by guardian'
      });
      
      // Update the UI to remove the denied trade
      setPendingTrades(pendingTrades.filter(trade => trade.trade_id !== tradeId));
      
      // Refresh guardian status to update counts
      const statusResponse = await api.get('/api/v1/family/guardian/status');
      setGuardianStatus(statusResponse.data);
    } catch (err: any) {
      console.error('Error denying trade:', err);
      alert('Failed to deny trade: ' + (err.message || 'Unknown error'));
    }
  };

  const handleAddFamilyMember = () => {
    setShowAddModal(true);
  };

  const handleScheduleTransfer = () => {
    navigate('/transfers');
  };

  const handleManagePermissions = () => {
    navigate('/settings/permissions');
  };

  const handleUpgradeSubscription = () => {
    navigate('/pricing');
  };

  // Chart options
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(17, 24, 39, 0.9)',
        borderColor: 'rgba(139, 92, 246, 0.5)',
        borderWidth: 1,
        titleFont: {
          size: 14
        },
        bodyFont: {
          size: 13
        },
        padding: 10,
        displayColors: false,
        callbacks: {
          label: function(context: any) {
            return `$${context.parsed.y.toFixed(2)}`;
          }
        }
      }
    },
    scales: {
      x: {
        grid: {
          display: false,
          drawBorder: false
        },
        ticks: {
          color: '#9ca3af',
          maxTicksLimit: 10
        }
      },
      y: {
        grid: {
          color: 'rgba(75, 85, 99, 0.2)',
          drawBorder: false
        },
        ticks: {
          color: '#9ca3af',
          callback: function(value: any) {
            return '$' + value;
          }
        }
      }
    },
    interaction: {
      mode: 'index',
      intersect: false
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-screen bg-gray-800">
        <div className="animate-spin rounded-full h-32 w-32 border-t-2 border-b-2 border-purple-500"></div>
      </div>
    );
  }
  
  // Error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-gray-800 p-6">
        <div className="bg-red-900 bg-opacity-25 p-6 rounded-lg text-white max-w-lg text-center">
          <h2 className="text-xl font-bold mb-4">Error Loading Family Dashboard</h2>
          <p className="mb-4">{error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg"
          >
            Reload Page
          </button>
        </div>
      </div>
    );
  }
  
  // Plan upgrade prompt if not on family plan
  if (!hasFamilyPlan) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-gray-800 p-6">
        <div className="bg-gradient-to-r from-purple-900 to-indigo-900 p-8 rounded-xl text-white max-w-xl text-center">
          <h2 className="text-2xl font-bold mb-4">Upgrade to Family Plan</h2>
          <p className="mb-6">You need to upgrade to our Family Premium plan to access the enhanced guardian dashboard and manage family accounts.</p>
          <div className="space-y-4 mb-8">
            <div className="flex items-center justify-center">
              <svg className="h-5 w-5 text-purple-300 mr-3" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"></path>
              </svg>
              <span className="text-purple-200">Add up to 5 custodial accounts</span>
            </div>
            <div className="flex items-center justify-center">
              <svg className="h-5 w-5 text-purple-300 mr-3" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"></path>
              </svg>
              <span className="text-purple-200">Age-appropriate education for minors</span>
            </div>
            <div className="flex items-center justify-center">
              <svg className="h-5 w-5 text-purple-300 mr-3" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"></path>
              </svg>
              <span className="text-purple-200">Guardian approval workflows</span>
            </div>
          </div>
          <button 
            onClick={handleUpgradeSubscription}
            className="bg-white text-purple-900 hover:bg-gray-100 font-medium rounded-full py-3 px-6 text-lg shadow-lg"
          >
            Upgrade Now
          </button>
        </div>
      </div>
    );
  }

  // Render the main dashboard
  return (
    <div className="flex flex-col">
      <div className="flex">
        {/* Sidebar */}
        <div className="w-[280px] bg-gray-900 min-h-screen p-4">
          <div className="pt-2 pb-6">
            <h2 className="text-xl font-bold text-white mb-4">Family Accounts</h2>
            
            {/* Guardian Info */}
            {guardian && (
              <div className="bg-gray-800 rounded-xl p-4 mb-6">
                <div className="flex items-center mb-3">
                  <div className={`h-10 w-10 rounded-full bg-${guardian.color}-600 flex items-center justify-center mr-3`}>
                    <span className="text-white font-bold">{guardian.initials}</span>
                  </div>
                  <div>
                    <h3 className="text-white font-medium">{guardian.name}</h3>
                    <p className="text-gray-400 text-sm">{guardian.role}</p>
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="flex items-center">
                    <span className="text-gray-400 text-sm mr-2">Family Members:</span>
                    <span className="text-gray-300 text-sm">{familyMembers.length + 1}</span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-gray-400 text-sm mr-2">Pending Approvals:</span>
                    <span className="text-gray-300 text-sm">{guardianStatus?.pending_approvals || 0}</span>
                  </div>
                </div>
              </div>
            )}
            
            {/* Family Members */}
            <h3 className="text-sm uppercase text-gray-500 font-semibold tracking-wide mb-3">Family Members</h3>
            <div className="space-y-2">
              {familyMembers.map((member) => (
                <div key={member.id} className="member-card bg-gray-800 rounded-lg p-3 flex items-center hover:bg-gray-700 transition-all cursor-pointer">
                  <div className={`h-8 w-8 rounded-full bg-${member.color}-600 flex items-center justify-center mr-3`}>
                    <span className="text-white font-bold text-sm">{member.initials}</span>
                  </div>
                  <div className="flex-1">
                    <h4 className="text-white text-sm font-medium">{member.name}</h4>
                    <p className="text-gray-400 text-xs">{member.role}</p>
                  </div>
                  <div className={`h-2 w-2 rounded-full ${
                    member.status === 'online' ? 'bg-green-500' : 
                    member.status === 'away' ? 'bg-yellow-500' : 'bg-gray-500'
                  }`}></div>
                </div>
              ))}
              
              {familyMembers.length === 0 && (
                <div className="text-center p-3 bg-gray-800 rounded-lg">
                  <p className="text-gray-400 text-sm">No family members yet</p>
                </div>
              )}
            </div>
            
            {/* Quick Actions */}
            <div className="mt-6 mb-6 border-t border-gray-800 pt-6">
              <h3 className="text-sm uppercase text-gray-500 font-semibold tracking-wide mb-3">Quick Actions</h3>
              <div className="space-y-2">
                <button 
                  onClick={handleAddFamilyMember}
                  className="w-full bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg p-2 text-sm text-left flex items-center"
                >
                  <svg className="h-5 w-5 mr-2 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                  </svg>
                  Add Family Member
                </button>
                <button 
                  onClick={handleScheduleTransfer}
                  className="w-full bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg p-2 text-sm text-left flex items-center"
                >
                  <svg className="h-5 w-5 mr-2 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                  Schedule Transfer
                </button>
                <button 
                  onClick={handleManagePermissions}
                  className="w-full bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg p-2 text-sm text-left flex items-center"
                >
                  <svg className="h-5 w-5 mr-2 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"></path>
                  </svg>
                  Manage Permissions
                </button>
              </div>
            </div>
            
            {/* 2FA Setup Banner - Only show if guardian doesn't have 2FA enabled and it's required */}
            {guardianStatus?.requires_2fa_setup && (
              <div className="bg-gradient-to-r from-yellow-800 to-orange-800 rounded-xl p-4 mb-6">
                <h3 className="text-white font-medium mb-2">Setup Two-Factor Authentication</h3>
                <p className="text-yellow-200 text-sm mb-3">For enhanced security, you must set up 2FA to manage family accounts.</p>
                <button 
                  onClick={() => navigate('/settings/security')}
                  className="w-full bg-white text-yellow-900 hover:bg-gray-100 font-medium rounded-full py-2 text-sm"
                >
                  Setup Now
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 bg-gray-800 min-h-screen p-6">
          {/* Header & Tabs */}
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-white mb-6">Family Investment Dashboard</h1>
            
            <div className="flex space-x-2 border-b border-gray-700">
              <button 
                onClick={() => handleTabChange('overview')}
                className={`tab-button px-4 py-2 text-sm font-medium ${
                  currentTab === 'overview' ? 'text-white border-b-2 border-purple-500' : 'text-gray-400'
                }`}
              >
                Overview
              </button>
              <button 
                onClick={() => handleTabChange('approval-requests')}
                className={`tab-button px-4 py-2 text-sm font-medium ${
                  currentTab === 'approval-requests' ? 'text-white border-b-2 border-purple-500' : 'text-gray-400'
                }`}
              >
                Approval Requests {pendingTrades.length > 0 && `(${pendingTrades.length})`}
              </button>
              <button 
                onClick={() => handleTabChange('educational-center')}
                className={`tab-button px-4 py-2 text-sm font-medium ${
                  currentTab === 'educational-center' ? 'text-white border-b-2 border-purple-500' : 'text-gray-400'
                }`}
              >
                Educational Center
              </button>
              <button 
                onClick={() => handleTabChange('settings')}
                className={`tab-button px-4 py-2 text-sm font-medium ${
                  currentTab === 'settings' ? 'text-white border-b-2 border-purple-500' : 'text-gray-400'
                }`}
              >
                Settings
              </button>
            </div>
          </div>

          {/* Overview Tab Content */}
          {currentTab === 'overview' && (
            <>
              {/* Family Overview */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                {/* Total Family Portfolio */}
                <div className="bg-gray-900 rounded-xl p-6 lg:col-span-2">
                  <div className="flex justify-between items-center mb-4">
                    <h2 className="text-lg font-medium text-white">Family Portfolio</h2>
                    <select 
                      className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1 text-sm text-white"
                      value={familyPortfolioTimeframe}
                      onChange={(e) => setFamilyPortfolioTimeframe(e.target.value as any)}
                    >
                      <option value="all">All Time</option>
                      <option value="year">This Year</option>
                      <option value="month">This Month</option>
                    </select>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <div>
                      <p className="text-gray-400 text-sm">Total Value</p>
                      <p className="text-2xl font-bold text-white">{formatCurrency(portfolioValue)}</p>
                    </div>
                    <div>
                      <p className="text-gray-400 text-sm">Growth (YTD)</p>
                      <div className="flex items-center">
                        <p className="text-2xl font-bold text-green-400">+{portfolioGrowth}%</p>
                        <svg className="h-5 w-5 ml-1 text-green-400" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                          <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd"></path>
                        </svg>
                      </div>
                    </div>
                    <div>
                      <p className="text-gray-400 text-sm">Total Accounts</p>
                      <p className="text-2xl font-bold text-white">{familyMembers.length + 1}</p>
                    </div>
                  </div>
                  
                  <div className="chart-container h-60">
                    <Line
                      ref={chartRef}
                      data={portfolioChartData}
                      options={chartOptions}
                    />
                  </div>
                </div>
                
                {/* Account Breakdown */}
                <div className="bg-gray-900 rounded-xl p-6">
                  <h2 className="text-lg font-medium text-white mb-4">Account Breakdown</h2>
                  
                  <div className="space-y-4">
                    {accountBreakdowns.map((account) => (
                      <div key={account.member.id} className="bg-gray-800 rounded-lg p-3">
                        <div className="flex justify-between items-center mb-2">
                          <div className="flex items-center">
                            <div className={`h-8 w-8 rounded-full bg-${account.member.color}-600 flex items-center justify-center mr-3`}>
                              <span className="text-white font-bold text-sm">{account.member.initials}</span>
                            </div>
                            <h3 className="text-white text-sm font-medium">{account.member.name}</h3>
                          </div>
                          <span className="text-gray-300 text-sm font-medium">{formatCurrency(account.balance)}</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2.5">
                          <div 
                            className={`bg-${account.member.color}-600 h-2.5 rounded-full`} 
                            style={{width: `${account.percentage}%`}}
                          ></div>
                        </div>
                        <div className="text-right mt-1">
                          <span className="text-gray-400 text-xs">{account.percentage}% of portfolio</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Approval Requests & Family Activity */}
              <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 mb-8">
                {/* Pending Requests */}
                <div className="bg-gray-900 rounded-xl p-6 lg:col-span-3">
                  <div className="flex justify-between items-center mb-4">
                    <h2 className="text-lg font-medium text-white">Pending Approval Requests</h2>
                    <div className="flex items-center">
                      <span className="inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-900 text-purple-200">
                        {pendingTrades.length} Pending
                      </span>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    {pendingTrades.length > 0 ? (
                      pendingTrades.map((trade) => {
                        // Find the corresponding minor for this trade
                        const minor = minors.find(m => m.id === trade.minor_id);
                        // Find the matching family member for display
                        const familyMember = familyMembers.find(f => f.id === `f-${trade.minor_id}`);
                        
                        return (
                          <div key={trade.trade_id} className="request-item bg-gray-800 rounded-lg p-4">
                            <div className="flex items-start justify-between mb-3">
                              <div className="flex items-center">
                                {familyMember && (
                                  <div className={`h-9 w-9 rounded-full bg-${familyMember.color}-600 flex items-center justify-center mr-3`}>
                                    <span className="text-white font-bold text-sm">{familyMember.initials}</span>
                                  </div>
                                )}
                                <div>
                                  <h3 className="text-white text-sm font-medium">{trade.minor_name}</h3>
                                  <p className="text-gray-400 text-xs">Requested {new Date(trade.created_at).toLocaleDateString()}</p>
                                </div>
                              </div>
                              <div className="px-2 py-1 bg-yellow-900 bg-opacity-30 rounded text-xs text-yellow-300">
                                Pending Approval
                              </div>
                            </div>
                            <div className="mb-4">
                              <h4 className="text-white text-sm font-medium mb-1">
                                {trade.trade_type.toUpperCase()} Request: {trade.symbol}
                              </h4>
                              <div className="flex flex-wrap gap-2">
                                <div className="bg-gray-700 rounded px-2 py-1 text-xs text-gray-300">
                                  Quantity: {trade.quantity}
                                </div>
                                <div className="bg-gray-700 rounded px-2 py-1 text-xs text-gray-300">
                                  Price: {formatCurrency(trade.price)}
                                </div>
                                <div className="bg-gray-700 rounded px-2 py-1 text-xs text-gray-300">
                                  Total: {formatCurrency(trade.quantity * trade.price)}
                                </div>
                              </div>
                            </div>
                            <div className="flex space-x-2">
                              <button 
                                onClick={() => handleApproveRequest(trade.trade_id)}
                                className="flex-1 bg-green-600 hover:bg-green-700 text-white rounded py-1.5 text-sm font-medium"
                              >
                                Approve
                              </button>
                              <button 
                                onClick={() => handleDenyRequest(trade.trade_id)}
                                className="flex-1 bg-gray-700 hover:bg-gray-600 text-white rounded py-1.5 text-sm font-medium"
                              >
                                Deny
                              </button>
                              <button 
                                onClick={() => navigate(`/family/minor/${trade.minor_id}/portfolio`)}
                                className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm"
                              >
                                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                                </svg>
                              </button>
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <div className="text-center py-8 bg-gray-800 rounded-lg">
                        <svg className="h-12 w-12 mx-auto text-gray-500 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                        <h3 className="text-white font-medium mb-1">No Pending Requests</h3>
                        <p className="text-gray-400 text-sm">All caught up! You'll be notified when there are new requests.</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Learning Progress Overview */}
                <div className="bg-gray-900 rounded-xl p-6 lg:col-span-2">
                  <div className="flex justify-between items-center mb-6">
                    <h2 className="text-lg font-medium text-white">Learning Progress</h2>
                    <button 
                      onClick={() => handleTabChange('educational-center')}
                      className="text-sm text-purple-400 hover:text-purple-300"
                    >
                      View All
                    </button>
                  </div>
                  
                  <div className="space-y-6">
                    {familyMembers.length > 0 ? (
                      familyMembers.slice(0, 2).map((member, index) => {
                        // Mock learning progress data
                        const progress = {
                          member,
                          progress: 50 + Math.floor(Math.random() * 40),
                          course: index === 0 ? 'Investing Basics' : 'Advanced Investing',
                          lessons: {
                            completed: index === 0 ? 12 : 15,
                            total: index === 0 ? 25 : 20
                          }
                        };
                        
                        return (
                          <div key={member.id}>
                            <div className="flex justify-between items-center mb-2">
                              <div className="flex items-center">
                                <div className={`h-8 w-8 rounded-full bg-${member.color}-600 flex items-center justify-center mr-3`}>
                                  <span className="text-white font-bold text-sm">{member.initials}</span>
                                </div>
                                <h3 className="text-white text-sm font-medium">{member.name}</h3>
                              </div>
                              <span className="text-gray-300 text-sm">{progress.progress}%</span>
                            </div>
                            <div className="relative pt-1">
                              <div className="flex mb-2 items-center justify-between">
                                <div>
                                  <span className="text-xs font-semibold inline-block text-purple-200">
                                    {progress.course}
                                  </span>
                                </div>
                                <div className="text-right">
                                  <span className="text-xs font-semibold inline-block text-purple-200">
                                    {progress.lessons.completed}/{progress.lessons.total} Lessons
                                  </span>
                                </div>
                              </div>
                              <div className="overflow-hidden h-2 mb-4 text-xs flex rounded bg-gray-700">
                                <div 
                                  style={{width: `${progress.progress}%`}} 
                                  className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-purple-500"
                                ></div>
                              </div>
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <div className="text-center py-6 bg-gray-800 rounded-lg">
                        <p className="text-gray-400 text-sm">No family members enrolled in courses yet.</p>
                      </div>
                    )}
                    
                    <div className="pt-2">
                      <h3 className="text-white text-sm font-medium mb-3">Recent Achievements</h3>
                      
                      <div className="grid grid-cols-3 gap-4">
                        {badges.map((badge) => (
                          <div key={badge.id} className={`badge-item ${badge.earned ? 'earned' : ''} bg-gray-800 p-3 rounded-lg text-center`}>
                            <div className={`h-12 w-12 bg-${badge.color}-900 rounded-full flex items-center justify-center mx-auto mb-2`}>
                              {badge.icon === 'lightbulb' && (
                                <svg className={`h-6 w-6 text-${badge.color}-300`} fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
                                </svg>
                              )}
                              {badge.icon === 'shield' && (
                                <svg className={`h-6 w-6 text-${badge.color}-300`} fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path>
                                </svg>
                              )}
                              {badge.icon === 'trending-up' && (
                                <svg className={`h-6 w-6 text-${badge.color}-300`} fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
                                </svg>
                              )}
                            </div>
                            <p className={`${badge.earned ? 'text-white' : 'text-gray-400'} text-xs`}>{badge.name}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Educational Events */}
              <div className="bg-gray-900 rounded-xl p-6">
                <h2 className="text-lg font-medium text-white mb-4">Upcoming Educational Events</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {educationalEvents.map((event, index) => (
                    <div key={index} className="flex items-start bg-gray-800 p-4 rounded-lg">
                      <div className="bg-purple-900 bg-opacity-40 rounded p-2 mr-3">
                        <span className="text-xs font-bold text-purple-300">{event.date}</span>
                      </div>
                      <div>
                        <h4 className="text-white text-sm font-medium">{event.title}</h4>
                        <p className="text-gray-400 text-xs">{event.description}</p>
                        <button className="mt-2 text-xs text-purple-400 hover:text-purple-300">
                          Add to Calendar
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* Approval Requests Tab Content */}
          {currentTab === 'approval-requests' && (
            <div className="bg-gray-900 rounded-xl p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-medium text-white">Pending Approval Requests</h2>
                <div className="flex items-center">
                  <span className="inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-900 text-purple-200">
                    {pendingTrades.length} Pending
                  </span>
                </div>
              </div>
              
              <div className="space-y-4">
                {pendingTrades.length > 0 ? (
                  pendingTrades.map((trade) => {
                    // Find the corresponding minor for this trade
                    const minor = minors.find(m => m.id === trade.minor_id);
                    // Find the matching family member for display
                    const familyMember = familyMembers.find(f => f.id === `f-${trade.minor_id}`);
                    
                    return (
                      <div key={trade.trade_id} className="request-item bg-gray-800 rounded-lg p-4">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center">
                            {familyMember && (
                              <div className={`h-9 w-9 rounded-full bg-${familyMember.color}-600 flex items-center justify-center mr-3`}>
                                <span className="text-white font-bold text-sm">{familyMember.initials}</span>
                              </div>
                            )}
                            <div>
                              <h3 className="text-white text-sm font-medium">{trade.minor_name}</h3>
                              <p className="text-gray-400 text-xs">Requested {new Date(trade.created_at).toLocaleDateString()}</p>
                            </div>
                          </div>
                          <div className="px-2 py-1 bg-yellow-900 bg-opacity-30 rounded text-xs text-yellow-300">
                            Pending Approval
                          </div>
                        </div>
                        <div className="mb-4">
                          <h4 className="text-white text-sm font-medium mb-1">
                            {trade.trade_type.toUpperCase()} Request: {trade.symbol}
                          </h4>
                          <div className="flex flex-wrap gap-2">
                            <div className="bg-gray-700 rounded px-2 py-1 text-xs text-gray-300">
                              Quantity: {trade.quantity}
                            </div>
                            <div className="bg-gray-700 rounded px-2 py-1 text-xs text-gray-300">
                              Price: {formatCurrency(trade.price)}
                            </div>
                            <div className="bg-gray-700 rounded px-2 py-1 text-xs text-gray-300">
                              Total: {formatCurrency(trade.quantity * trade.price)}
                            </div>
                          </div>
                        </div>
                        <div className="flex space-x-2">
                          <button 
                            onClick={() => handleApproveRequest(trade.trade_id)}
                            className="flex-1 bg-green-600 hover:bg-green-700 text-white rounded py-1.5 text-sm font-medium"
                          >
                            Approve
                          </button>
                          <button 
                            onClick={() => handleDenyRequest(trade.trade_id)}
                            className="flex-1 bg-gray-700 hover:bg-gray-600 text-white rounded py-1.5 text-sm font-medium"
                          >
                            Deny
                          </button>
                          <button 
                            onClick={() => navigate(`/family/minor/${trade.minor_id}/portfolio`)}
                            className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm"
                          >
                            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                            </svg>
                          </button>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="text-center py-16 bg-gray-800 rounded-lg">
                    <svg className="h-16 w-16 mx-auto text-gray-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <h3 className="text-white text-lg font-medium mb-2">No Pending Requests</h3>
                    <p className="text-gray-400 max-w-md mx-auto">All caught up! You'll be notified when there are new trade requests that need your approval.</p>
                  </div>
                )}
              </div>
            </div>
          )}
          
          {/* Educational Center Tab Content */}
          {currentTab === 'educational-center' && (
            <div className="bg-gray-900 rounded-xl p-6">
              <h2 className="text-xl font-medium text-white mb-6">Family Educational Center</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-medium text-white mb-4">Learning Progress</h3>
                  
                  <div className="space-y-6">
                    {familyMembers.length > 0 ? (
                      familyMembers.map((member, index) => {
                        // Mock learning progress data
                        const progress = {
                          member,
                          progress: 50 + Math.floor(Math.random() * 40),
                          course: index === 0 ? 'Investing Basics' : 'Advanced Investing',
                          lessons: {
                            completed: index === 0 ? 12 : 15,
                            total: index === 0 ? 25 : 20
                          }
                        };
                        
                        return (
                          <div key={member.id} className="bg-gray-800 rounded-lg p-4">
                            <div className="flex justify-between items-center mb-3">
                              <div className="flex items-center">
                                <div className={`h-8 w-8 rounded-full bg-${member.color}-600 flex items-center justify-center mr-3`}>
                                  <span className="text-white font-bold text-sm">{member.initials}</span>
                                </div>
                                <h3 className="text-white text-sm font-medium">{member.name}</h3>
                              </div>
                              <span className="text-gray-300 text-sm">{progress.progress}%</span>
                            </div>
                            <div className="relative pt-1">
                              <div className="flex mb-2 items-center justify-between">
                                <div>
                                  <span className="text-xs font-semibold inline-block text-purple-200">
                                    {progress.course}
                                  </span>
                                </div>
                                <div className="text-right">
                                  <span className="text-xs font-semibold inline-block text-purple-200">
                                    {progress.lessons.completed}/{progress.lessons.total} Lessons
                                  </span>
                                </div>
                              </div>
                              <div className="overflow-hidden h-2 mb-4 text-xs flex rounded bg-gray-700">
                                <div 
                                  style={{width: `${progress.progress}%`}} 
                                  className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-purple-500"
                                ></div>
                              </div>
                            </div>
                            <button 
                              onClick={() => navigate(`/learning/${member.id}`)}
                              className="w-full bg-purple-700 hover:bg-purple-600 text-white rounded py-2 text-sm"
                            >
                              View Progress
                            </button>
                          </div>
                        );
                      })
                    ) : (
                      <div className="text-center py-6 bg-gray-800 rounded-lg">
                        <p className="text-gray-400 text-sm">No family members enrolled in courses yet.</p>
                        <button 
                          onClick={handleAddFamilyMember}
                          className="mt-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg px-4 py-2 text-sm"
                        >
                          Add Family Member
                        </button>
                      </div>
                    )}
                  </div>
                </div>
                
                <div>
                  <h3 className="text-lg font-medium text-white mb-4">Upcoming Events</h3>
                  
                  <div className="bg-gray-800 p-5 rounded-lg mb-6">
                    <h4 className="text-white font-medium mb-4">Educational Calendar</h4>
                    
                    <div className="space-y-4">
                      {educationalEvents.map((event, index) => (
                        <div key={index} className="flex items-start bg-gray-700 p-3 rounded-lg">
                          <div className="bg-purple-900 bg-opacity-40 rounded p-2 mr-3">
                            <span className="text-xs font-bold text-purple-300">{event.date}</span>
                          </div>
                          <div>
                            <h4 className="text-white text-sm font-medium">{event.title}</h4>
                            <p className="text-gray-400 text-xs">{event.description}</p>
                            <button className="mt-2 text-xs text-purple-400 hover:text-purple-300">
                              Add to Calendar
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                    
                    <button 
                      onClick={() => navigate('/learning/events')}
                      className="w-full bg-gray-700 hover:bg-gray-600 text-white rounded-lg p-2 text-sm mt-4"
                    >
                      View All Events
                    </button>
                  </div>
                  
                  <div className="bg-gray-800 p-5 rounded-lg">
                    <h4 className="text-white font-medium mb-4">Recommended Courses</h4>
                    
                    <div className="space-y-3">
                      <div className="bg-gray-700 p-3 rounded-lg">
                        <h5 className="text-white text-sm font-medium">Advanced Stock Analysis</h5>
                        <p className="text-gray-400 text-xs mb-2">Learn how to analyze stocks like a professional.</p>
                        <div className="flex justify-between">
                          <span className="text-xs text-gray-400">12 lessons</span>
                          <span className="text-xs text-purple-400">Ages 14+</span>
                        </div>
                      </div>
                      
                      <div className="bg-gray-700 p-3 rounded-lg">
                        <h5 className="text-white text-sm font-medium">Financial Independence 101</h5>
                        <p className="text-gray-400 text-xs mb-2">Teaching kids about saving, investing, and building wealth.</p>
                        <div className="flex justify-between">
                          <span className="text-xs text-gray-400">8 lessons</span>
                          <span className="text-xs text-purple-400">Ages 10+</span>
                        </div>
                      </div>
                      
                      <div className="bg-gray-700 p-3 rounded-lg">
                        <h5 className="text-white text-sm font-medium">Crypto for Beginners</h5>
                        <p className="text-gray-400 text-xs mb-2">Understanding digital currencies and blockchain.</p>
                        <div className="flex justify-between">
                          <span className="text-xs text-gray-400">10 lessons</span>
                          <span className="text-xs text-purple-400">Ages 12+</span>
                        </div>
                      </div>
                    </div>
                    
                    <button 
                      onClick={() => navigate('/learning/courses')}
                      className="w-full bg-purple-600 hover:bg-purple-700 text-white rounded-lg p-2 text-sm mt-4"
                    >
                      Browse All Courses
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {/* Settings Tab Content */}
          {currentTab === 'settings' && (
            <div className="bg-gray-900 rounded-xl p-6">
              <h2 className="text-xl font-medium text-white mb-6">Family Account Settings</h2>
              
              <div className="space-y-6">
                <div className="bg-gray-800 p-5 rounded-lg">
                  <h3 className="text-lg font-medium text-white mb-4">Approval Settings</h3>
                  
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <h4 className="text-white text-sm font-medium">Auto-approve small purchases</h4>
                        <p className="text-gray-400 text-xs">Automatically approve purchases under $25</p>
                      </div>
                      <div className="relative inline-block w-12 h-6 bg-gray-700 rounded-full cursor-pointer">
                        <input type="checkbox" id="toggle-auto-approve" className="sr-only" defaultChecked />
                        <span className="block w-6 h-6 bg-purple-600 rounded-full transform translate-x-6 transition"></span>
                      </div>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <div>
                        <h4 className="text-white text-sm font-medium">Require dual approval</h4>
                        <p className="text-gray-400 text-xs">Require approval from both guardians</p>
                      </div>
                      <div className="relative inline-block w-12 h-6 bg-gray-700 rounded-full cursor-pointer">
                        <input type="checkbox" id="toggle-dual-approval" className="sr-only" />
                        <span className="block w-6 h-6 bg-gray-500 rounded-full transition"></span>
                      </div>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <div>
                        <h4 className="text-white text-sm font-medium">Email notifications</h4>
                        <p className="text-gray-400 text-xs">Send email for new approval requests</p>
                      </div>
                      <div className="relative inline-block w-12 h-6 bg-gray-700 rounded-full cursor-pointer">
                        <input type="checkbox" id="toggle-email-notifications" className="sr-only" defaultChecked />
                        <span className="block w-6 h-6 bg-purple-600 rounded-full transform translate-x-6 transition"></span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-800 p-5 rounded-lg">
                  <h3 className="text-lg font-medium text-white mb-4">Investment Restrictions</h3>
                  
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-white text-sm font-medium mb-2">Restricted Asset Classes</h4>
                      <div className="flex flex-wrap gap-2">
                        <div className="bg-gray-700 px-3 py-1 rounded-full text-sm text-gray-300 flex items-center">
                          Options
                          <svg className="h-4 w-4 ml-2 text-gray-500" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd"></path>
                          </svg>
                        </div>
                        <div className="bg-gray-700 px-3 py-1 rounded-full text-sm text-gray-300 flex items-center">
                          Futures
                          <svg className="h-4 w-4 ml-2 text-gray-500" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd"></path>
                          </svg>
                        </div>
                        <div className="bg-gray-700 px-3 py-1 rounded-full text-sm text-gray-300 flex items-center">
                          Margin Trading
                          <svg className="h-4 w-4 ml-2 text-gray-500" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd"></path>
                          </svg>
                        </div>
                        <button className="bg-gray-700 px-3 py-1 rounded-full text-sm text-purple-400 hover:bg-gray-600">
                          + Add Restriction
                        </button>
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="text-white text-sm font-medium mb-2">Trading Limits</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="text-gray-400 text-xs mb-1 block">Max Single Transaction</label>
                          <input 
                            type="text" 
                            defaultValue="$500.00" 
                            className="bg-gray-700 border border-gray-600 text-white rounded py-2 px-3 w-full"
                          />
                        </div>
                        <div>
                          <label className="text-gray-400 text-xs mb-1 block">Max Daily Transactions</label>
                          <input 
                            type="text" 
                            defaultValue="$1,000.00" 
                            className="bg-gray-700 border border-gray-600 text-white rounded py-2 px-3 w-full"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <button className="mt-4 bg-purple-600 hover:bg-purple-700 text-white rounded px-4 py-2 text-sm font-medium">
                    Save Settings
                  </button>
                </div>
                
                <div className="bg-gray-800 p-5 rounded-lg">
                  <h3 className="text-lg font-medium text-white mb-4">Security Settings</h3>
                  
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <h4 className="text-white text-sm font-medium">Two-Factor Authentication</h4>
                        <p className="text-gray-400 text-xs">Require 2FA for all guardian actions</p>
                      </div>
                      <div className="relative inline-block w-12 h-6 bg-gray-700 rounded-full cursor-pointer">
                        <input 
                          type="checkbox" 
                          id="toggle-2fa" 
                          className="sr-only"
                          defaultChecked={guardianStatus?.two_factor_enabled}
                        />
                        <span className={`block w-6 h-6 ${guardianStatus?.two_factor_enabled ? 'bg-purple-600 transform translate-x-6' : 'bg-gray-500'} rounded-full transition`}></span>
                      </div>
                    </div>
                    
                    {!guardianStatus?.two_factor_enabled && (
                      <button 
                        onClick={() => navigate('/settings/security')}
                        className="w-full bg-purple-600 hover:bg-purple-700 text-white rounded py-2 text-sm"
                      >
                        Setup Two-Factor Authentication
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EnhancedGuardianDashboard;