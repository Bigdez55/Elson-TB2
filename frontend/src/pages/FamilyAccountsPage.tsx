import React, { useState, useEffect } from 'react';
import { Badge } from '../components/common/Badge';
import { Skeleton, SkeletonStatsCard, SkeletonListItem } from '../components/common/Skeleton';

interface FamilyMember {
  id: string;
  name: string;
  email: string;
  role: 'owner' | 'adult' | 'teen' | 'child';
  status: 'active' | 'pending' | 'restricted';
  avatar: string;
  portfolioValue: number;
  monthlyChange: number;
  accountType: string;
}

interface PendingApproval {
  id: string;
  memberName: string;
  action: string;
  details: string;
  timestamp: string;
  amount?: number;
}

interface ActivityItem {
  id: string;
  memberName: string;
  action: string;
  timestamp: string;
  icon: 'trade' | 'deposit' | 'approval' | 'settings';
}

const FamilyAccountsPage: React.FC = () => {
  const [showAddMemberModal, setShowAddMemberModal] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [newMemberData, setNewMemberData] = useState({
    name: '',
    email: '',
    role: 'adult',
    accountType: 'individual'
  });

  // Simulate loading for future API integration
  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 800);
    return () => clearTimeout(timer);
  }, []);

  // Mock data - replace with API calls
  const familyMembers: FamilyMember[] = [
    {
      id: '1',
      name: 'Alex Morgan',
      email: 'alex@example.com',
      role: 'owner',
      status: 'active',
      avatar: 'AM',
      portfolioValue: 34567.89,
      monthlyChange: 4.3,
      accountType: 'Primary'
    },
    {
      id: '2',
      name: 'Sarah Morgan',
      email: 'sarah@example.com',
      role: 'adult',
      status: 'active',
      avatar: 'SM',
      portfolioValue: 12450.00,
      monthlyChange: 2.8,
      accountType: 'Individual'
    },
    {
      id: '3',
      name: 'Jake Morgan',
      email: 'jake@example.com',
      role: 'teen',
      status: 'active',
      avatar: 'JM',
      portfolioValue: 2150.75,
      monthlyChange: 5.2,
      accountType: 'Custodial'
    },
    {
      id: '4',
      name: 'Emma Morgan',
      email: 'emma@example.com',
      role: 'child',
      status: 'restricted',
      avatar: 'EM',
      portfolioValue: 850.00,
      monthlyChange: 1.5,
      accountType: 'UGMA'
    }
  ];

  const pendingApprovals: PendingApproval[] = [
    {
      id: '1',
      memberName: 'Jake Morgan',
      action: 'Stock Purchase Request',
      details: 'Requesting to buy 5 shares of AAPL',
      timestamp: '2 hours ago',
      amount: 875.50
    },
    {
      id: '2',
      memberName: 'Emma Morgan',
      action: 'Account Access Request',
      details: 'Requesting to enable trading features',
      timestamp: '1 day ago'
    }
  ];

  const recentActivity: ActivityItem[] = [
    {
      id: '1',
      memberName: 'Sarah Morgan',
      action: 'Deposited $500 into account',
      timestamp: '30 minutes ago',
      icon: 'deposit'
    },
    {
      id: '2',
      memberName: 'Jake Morgan',
      action: 'Bought 2 shares of MSFT',
      timestamp: '2 hours ago',
      icon: 'trade'
    },
    {
      id: '3',
      memberName: 'Alex Morgan',
      action: 'Approved withdrawal request',
      timestamp: '5 hours ago',
      icon: 'approval'
    },
    {
      id: '4',
      memberName: 'Emma Morgan',
      action: 'Updated notification preferences',
      timestamp: '1 day ago',
      icon: 'settings'
    }
  ];

  const totalFamilyValue = familyMembers.reduce((sum, member) => sum + member.portfolioValue, 0);
  const avgMonthlyGrowth = familyMembers.reduce((sum, member) => sum + member.monthlyChange, 0) / familyMembers.length;

  const getRoleBadgeVariant = (role: string) => {
    switch (role) {
      case 'owner': return 'premium';
      case 'adult': return 'info';
      case 'teen': return 'warning';
      case 'child': return 'neutral';
      default: return 'neutral';
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'pending': return 'warning';
      case 'restricted': return 'error';
      default: return 'neutral';
    }
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'trade':
        return (
          <svg className="h-5 w-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
        );
      case 'deposit':
        return (
          <svg className="h-5 w-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
        );
      case 'approval':
        return (
          <svg className="h-5 w-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
          </svg>
        );
      case 'settings':
        return (
          <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        );
      default:
        return null;
    }
  };

  const handleAddMember = () => {
    console.log('Adding member:', newMemberData);
    setShowAddMemberModal(false);
    setNewMemberData({ name: '', email: '', role: 'adult', accountType: 'individual' });
  };

  const handleApprove = (approvalId: string) => {
    console.log('Approving:', approvalId);
  };

  const handleDeny = (approvalId: string) => {
    console.log('Denying:', approvalId);
  };

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="bg-gray-800 min-h-screen p-6">
        {/* Header Skeleton */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <Skeleton variant="text" width="200px" height="32px" className="mb-2" />
            <Skeleton variant="text" width="300px" height="20px" />
          </div>
          <Skeleton variant="rectangular" width="180px" height="42px" className="rounded-lg" />
        </div>

        {/* Family Overview Stats Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          {[1, 2, 3, 4].map((i) => (
            <SkeletonStatsCard key={i} />
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Family Members List Skeleton */}
          <div className="lg:col-span-2">
            <div className="bg-gray-900 rounded-xl p-6">
              <Skeleton variant="text" width="150px" height="24px" className="mb-6" />
              <div className="space-y-4">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
                    <div className="flex items-center gap-4">
                      <Skeleton variant="circular" width="48px" height="48px" />
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <Skeleton variant="text" width="120px" height="20px" />
                          <Skeleton variant="rectangular" width="50px" height="20px" className="rounded" />
                          <Skeleton variant="rectangular" width="50px" height="20px" className="rounded" />
                        </div>
                        <Skeleton variant="text" width="180px" height="16px" className="mb-1" />
                        <Skeleton variant="text" width="100px" height="12px" />
                      </div>
                    </div>
                    <div className="text-right">
                      <Skeleton variant="text" width="100px" height="20px" className="mb-1" />
                      <Skeleton variant="text" width="80px" height="16px" />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Pending Approvals Skeleton */}
            <div className="bg-gray-900 rounded-xl p-6 mt-6">
              <Skeleton variant="text" width="180px" height="24px" className="mb-6" />
              <div className="space-y-4">
                {[1, 2].map((i) => (
                  <div key={i} className="p-4 bg-gray-800 rounded-lg">
                    <div className="flex justify-between mb-3">
                      <div>
                        <Skeleton variant="text" width="160px" height="20px" className="mb-1" />
                        <Skeleton variant="text" width="100px" height="16px" />
                      </div>
                      <Skeleton variant="text" width="80px" height="14px" />
                    </div>
                    <Skeleton variant="text" width="100%" height="16px" className="mb-3" />
                    <div className="flex gap-3">
                      <Skeleton variant="rectangular" width="100%" height="40px" className="rounded-lg" />
                      <Skeleton variant="rectangular" width="100%" height="40px" className="rounded-lg" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Activity Feed Skeleton */}
          <div>
            <div className="bg-gray-900 rounded-xl p-6">
              <Skeleton variant="text" width="150px" height="24px" className="mb-6" />
              <div className="space-y-4">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="flex items-start gap-3">
                    <Skeleton variant="circular" width="40px" height="40px" />
                    <div className="flex-1">
                      <Skeleton variant="text" width="100px" height="16px" className="mb-1" />
                      <Skeleton variant="text" width="100%" height="14px" className="mb-1" />
                      <Skeleton variant="text" width="60px" height="12px" />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Actions Skeleton */}
            <div className="bg-gray-900 rounded-xl p-6 mt-6">
              <Skeleton variant="text" width="120px" height="24px" className="mb-4" />
              <div className="space-y-3">
                {[1, 2, 3, 4].map((i) => (
                  <Skeleton key={i} variant="rectangular" width="100%" height="48px" className="rounded-lg" />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 min-h-screen p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Family Accounts</h1>
          <p className="text-gray-400">Manage your family's investment accounts</p>
        </div>
        <button
          onClick={() => setShowAddMemberModal(true)}
          className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg flex items-center transition-colors"
        >
          <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Add Family Member
        </button>
      </div>

      {/* Family Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-gray-900 rounded-xl p-6">
          <p className="text-gray-400 text-sm mb-1">Total Family Value</p>
          <p className="text-2xl font-bold text-white">${totalFamilyValue.toLocaleString()}</p>
          <p className="text-green-400 text-sm mt-1">+{avgMonthlyGrowth.toFixed(1)}% this month</p>
        </div>
        <div className="bg-gray-900 rounded-xl p-6">
          <p className="text-gray-400 text-sm mb-1">Family Members</p>
          <p className="text-2xl font-bold text-white">{familyMembers.length}</p>
          <p className="text-gray-400 text-sm mt-1">of 5 available</p>
        </div>
        <div className="bg-gray-900 rounded-xl p-6">
          <p className="text-gray-400 text-sm mb-1">Pending Approvals</p>
          <p className="text-2xl font-bold text-white">{pendingApprovals.length}</p>
          <p className="text-yellow-400 text-sm mt-1">Requires attention</p>
        </div>
        <div className="bg-gray-900 rounded-xl p-6">
          <p className="text-gray-400 text-sm mb-1">Total Contributions</p>
          <p className="text-2xl font-bold text-white">$2,450</p>
          <p className="text-gray-400 text-sm mt-1">This month</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Family Members List */}
        <div className="lg:col-span-2">
          <div className="bg-gray-900 rounded-xl p-6">
            <h2 className="text-lg font-semibold text-white mb-6">Family Members</h2>
            <div className="space-y-4">
              {familyMembers.map((member) => (
                <div
                  key={member.id}
                  className="flex items-center justify-between p-4 bg-gray-800 rounded-lg hover:bg-gray-750 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className="h-12 w-12 rounded-full bg-gradient-to-r from-purple-600 to-blue-500 flex items-center justify-center">
                      <span className="text-white font-bold">{member.avatar}</span>
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="text-white font-medium">{member.name}</p>
                        <Badge variant={getRoleBadgeVariant(member.role)} size="sm">
                          {member.role.charAt(0).toUpperCase() + member.role.slice(1)}
                        </Badge>
                        <Badge variant={getStatusBadgeVariant(member.status)} size="sm">
                          {member.status.charAt(0).toUpperCase() + member.status.slice(1)}
                        </Badge>
                      </div>
                      <p className="text-gray-400 text-sm">{member.email}</p>
                      <p className="text-gray-500 text-xs">{member.accountType} Account</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-white font-medium">${member.portfolioValue.toLocaleString()}</p>
                    <p className={`text-sm ${member.monthlyChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {member.monthlyChange >= 0 ? '+' : ''}{member.monthlyChange}% this month
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Pending Approvals */}
          {pendingApprovals.length > 0 && (
            <div className="bg-gray-900 rounded-xl p-6 mt-6">
              <h2 className="text-lg font-semibold text-white mb-6 flex items-center">
                <span className="h-2 w-2 bg-yellow-400 rounded-full mr-2"></span>
                Pending Approvals
              </h2>
              <div className="space-y-4">
                {pendingApprovals.map((approval) => (
                  <div
                    key={approval.id}
                    className="p-4 bg-gray-800 rounded-lg border border-yellow-900/50"
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <p className="text-white font-medium">{approval.action}</p>
                        <p className="text-gray-400 text-sm">{approval.memberName}</p>
                      </div>
                      <span className="text-gray-500 text-xs">{approval.timestamp}</span>
                    </div>
                    <p className="text-gray-300 text-sm mb-3">{approval.details}</p>
                    {approval.amount && (
                      <p className="text-white font-medium mb-3">Amount: ${approval.amount.toFixed(2)}</p>
                    )}
                    <div className="flex gap-3">
                      <button
                        onClick={() => handleApprove(approval.id)}
                        className="flex-1 bg-green-600 hover:bg-green-700 text-white py-2 rounded-lg text-sm transition-colors"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => handleDeny(approval.id)}
                        className="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-2 rounded-lg text-sm transition-colors"
                      >
                        Deny
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Activity Feed */}
        <div>
          <div className="bg-gray-900 rounded-xl p-6">
            <h2 className="text-lg font-semibold text-white mb-6">Recent Activity</h2>
            <div className="space-y-4">
              {recentActivity.map((activity) => (
                <div key={activity.id} className="flex items-start gap-3">
                  <div className="h-10 w-10 rounded-full bg-gray-800 flex items-center justify-center flex-shrink-0">
                    {getActivityIcon(activity.icon)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white text-sm">{activity.memberName}</p>
                    <p className="text-gray-400 text-sm truncate">{activity.action}</p>
                    <p className="text-gray-500 text-xs">{activity.timestamp}</p>
                  </div>
                </div>
              ))}
            </div>
            <button className="w-full mt-6 text-purple-400 hover:text-purple-300 text-sm transition-colors">
              View All Activity
            </button>
          </div>

          {/* Quick Actions */}
          <div className="bg-gray-900 rounded-xl p-6 mt-6">
            <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <button className="w-full flex items-center gap-3 p-3 bg-gray-800 hover:bg-gray-750 rounded-lg text-left transition-colors">
                <svg className="h-5 w-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-gray-300 text-sm">Transfer Between Accounts</span>
              </button>
              <button className="w-full flex items-center gap-3 p-3 bg-gray-800 hover:bg-gray-750 rounded-lg text-left transition-colors">
                <svg className="h-5 w-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <span className="text-gray-300 text-sm">Set Spending Limits</span>
              </button>
              <button className="w-full flex items-center gap-3 p-3 bg-gray-800 hover:bg-gray-750 rounded-lg text-left transition-colors">
                <svg className="h-5 w-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                <span className="text-gray-300 text-sm">Manage Notifications</span>
              </button>
              <button className="w-full flex items-center gap-3 p-3 bg-gray-800 hover:bg-gray-750 rounded-lg text-left transition-colors">
                <svg className="h-5 w-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <span className="text-gray-300 text-sm">Download Family Report</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Add Member Modal */}
      {showAddMemberModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 rounded-xl p-6 w-full max-w-md mx-4">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-white">Add Family Member</h2>
              <button
                onClick={() => setShowAddMemberModal(false)}
                className="text-gray-400 hover:text-white"
              >
                <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-gray-400 text-sm mb-1">Full Name</label>
                <input
                  type="text"
                  value={newMemberData.name}
                  onChange={(e) => setNewMemberData({ ...newMemberData, name: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
                  placeholder="Enter full name"
                />
              </div>

              <div>
                <label className="block text-gray-400 text-sm mb-1">Email Address</label>
                <input
                  type="email"
                  value={newMemberData.email}
                  onChange={(e) => setNewMemberData({ ...newMemberData, email: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
                  placeholder="Enter email address"
                />
              </div>

              <div>
                <label className="block text-gray-400 text-sm mb-1">Role</label>
                <select
                  value={newMemberData.role}
                  onChange={(e) => setNewMemberData({ ...newMemberData, role: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
                >
                  <option value="adult">Adult</option>
                  <option value="teen">Teen (13-17)</option>
                  <option value="child">Child (Under 13)</option>
                </select>
              </div>

              <div>
                <label className="block text-gray-400 text-sm mb-1">Account Type</label>
                <select
                  value={newMemberData.accountType}
                  onChange={(e) => setNewMemberData({ ...newMemberData, accountType: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
                >
                  <option value="individual">Individual</option>
                  <option value="custodial">Custodial (UTMA)</option>
                  <option value="ugma">UGMA</option>
                </select>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowAddMemberModal(false)}
                className="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-3 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleAddMember}
                className="flex-1 bg-purple-600 hover:bg-purple-700 text-white py-3 rounded-lg transition-colors"
              >
                Send Invitation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FamilyAccountsPage;
