import React from 'react';
import { Link } from 'react-router-dom';

const FamilyAccountsPage: React.FC = () => {
  return (
    <div className="bg-gray-800 min-h-screen p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Family Accounts</h1>
        <p className="text-gray-400">Manage your family's investment accounts</p>
      </div>

      {/* Coming Soon Banner */}
      <div className="max-w-2xl mx-auto">
        <div className="bg-gradient-to-r from-purple-900/40 to-blue-900/40 rounded-2xl p-8 border border-purple-500/30 text-center">
          <div className="w-20 h-20 bg-purple-600/30 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-10 h-10 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>

          <h2 className="text-2xl font-bold text-white mb-3">Family Accounts Coming Soon</h2>
          <p className="text-gray-300 mb-6 max-w-md mx-auto">
            We're building powerful family account features to help you manage investments for your whole family.
            Add family members, set spending limits, and track everyone's progress.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="bg-gray-800/50 rounded-lg p-4">
              <div className="text-purple-400 text-2xl mb-2">👨‍👩‍👧‍👦</div>
              <h3 className="text-white font-medium mb-1">Multi-Member Access</h3>
              <p className="text-gray-400 text-sm">Add adults, teens, and children to your family plan</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-4">
              <div className="text-purple-400 text-2xl mb-2">🔒</div>
              <h3 className="text-white font-medium mb-1">Parental Controls</h3>
              <p className="text-gray-400 text-sm">Approve trades and set spending limits</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-4">
              <div className="text-purple-400 text-2xl mb-2">📊</div>
              <h3 className="text-white font-medium mb-1">Family Dashboard</h3>
              <p className="text-gray-400 text-sm">Track all family portfolios in one place</p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-medium transition-colors">
              Join the Waitlist
            </button>
            <Link
              to="/dashboard"
              className="bg-gray-700 hover:bg-gray-600 text-white px-6 py-3 rounded-lg font-medium transition-colors"
            >
              Back to Dashboard
            </Link>
          </div>
        </div>

        {/* FAQ Section */}
        <div className="mt-8 bg-gray-900 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Frequently Asked Questions</h3>
          <div className="space-y-4">
            <div>
              <h4 className="text-white font-medium mb-1">When will Family Accounts be available?</h4>
              <p className="text-gray-400 text-sm">We're working hard to launch Family Accounts soon. Join the waitlist to be notified!</p>
            </div>
            <div>
              <h4 className="text-white font-medium mb-1">How many family members can I add?</h4>
              <p className="text-gray-400 text-sm">Family plans will support up to 5 family members with different permission levels.</p>
            </div>
            <div>
              <h4 className="text-white font-medium mb-1">Will there be custodial accounts for minors?</h4>
              <p className="text-gray-400 text-sm">Yes! We'll offer UTMA/UGMA custodial accounts for children with full parental oversight.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FamilyAccountsPage;
