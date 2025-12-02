import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../../app/store/store';
import { Switch } from '../../app/components/common/Switch';
import { Button } from '../../app/components/common/Button';
import LoadingSpinner from '../../app/components/common/LoadingSpinner';
import FamilyService, { MinorAccountWithPermissions } from '../../app/services/familyService';
import { toast } from 'react-toastify';

interface PermissionChange {
  accountId: number;
  permission: string;
  value: boolean;
}

const GuardianPermissions: React.FC = () => {
  const [minorAccounts, setMinorAccounts] = useState<MinorAccountWithPermissions[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [pendingChanges, setPendingChanges] = useState<Record<string, Record<string, boolean>>>({});
  const user = useSelector((state: RootState) => state.user.user);

  // Fetch accounts with permissions
  useEffect(() => {
    const fetchMinorAccounts = async () => {
      setLoading(true);
      try {
        const accounts = await FamilyService.getMinorAccountsWithPermissions();
        setMinorAccounts(accounts);
        // Initialize empty pending changes object
        const initialPendingChanges: Record<string, Record<string, boolean>> = {};
        accounts.forEach(account => {
          initialPendingChanges[account.id] = {};
        });
        setPendingChanges(initialPendingChanges);
      } catch (error) {
        console.error('Error fetching minor accounts:', error);
        toast.error('Failed to load minor accounts. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchMinorAccounts();
  }, []);

  const handlePermissionChange = (accountId: number, permission: string, value: boolean) => {
    // Update the pending changes
    setPendingChanges(prevChanges => ({
      ...prevChanges,
      [accountId]: {
        ...prevChanges[accountId],
        [permission]: value
      }
    }));

    // Update the UI immediately
    setMinorAccounts(accounts => 
      accounts.map(account => 
        account.id === accountId 
          ? { 
              ...account, 
              permissions: { 
                ...account.permissions, 
                [permission]: value 
              } 
            }
          : account
      )
    );
  };

  const hasChanges = () => {
    // Check if there are any pending changes
    return Object.keys(pendingChanges).some(accountId => 
      Object.keys(pendingChanges[accountId]).length > 0
    );
  };

  const savePermissions = async () => {
    setSaving(true);
    try {
      // Save each account with changes
      for (const accountId in pendingChanges) {
        if (Object.keys(pendingChanges[accountId]).length > 0) {
          // Convert string accountId to number
          const numericAccountId = parseInt(accountId, 10);
          await FamilyService.updateMinorPermissions(numericAccountId, pendingChanges[accountId]);
        }
      }
      
      // Clear pending changes
      const emptyChanges: Record<string, Record<string, boolean>> = {};
      minorAccounts.forEach(account => {
        emptyChanges[account.id] = {};
      });
      setPendingChanges(emptyChanges);
      
      // Show success message
      toast.success('Permissions saved successfully');
    } catch (error) {
      console.error('Error saving permissions:', error);
      toast.error('Failed to save permissions. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center p-8">
        <LoadingSpinner size="large" color="text-purple-600" text="Loading permissions..." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Minor Account Permissions</h1>
        <Button 
          onClick={savePermissions} 
          disabled={saving || !hasChanges()} 
          className="bg-purple-600 hover:bg-purple-700"
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </Button>
      </div>

      {minorAccounts.length === 0 ? (
        <div className="bg-gray-800 p-6 rounded-lg text-center">
          <p className="text-gray-400">You don't have any minor accounts to manage.</p>
          <Button 
            className="mt-4 bg-blue-600 hover:bg-blue-700" 
            onClick={() => window.location.href = '/family/dashboard'}
          >
            Add Minor Account
          </Button>
        </div>
      ) : (
        <div className="space-y-6">
          {minorAccounts.map(account => (
            <div key={account.id} className="bg-gray-800 p-6 rounded-lg">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h2 className="text-xl font-semibold">{account.firstName} {account.lastName}</h2>
                  <p className="text-gray-400">{account.email} • {account.ageInYears} years old</p>
                </div>
                <Button 
                  className="text-sm bg-transparent border border-gray-600 hover:bg-gray-700"
                  onClick={() => window.location.href = `/family/dashboard?minorId=${account.id}`}
                >
                  View Profile
                </Button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex justify-between items-center p-3 border border-gray-700 rounded-lg">
                  <div>
                    <p className="font-medium">Trading Access</p>
                    <p className="text-sm text-gray-400">Allow trading on the platform</p>
                  </div>
                  <Switch 
                    checked={account.permissions.trading}
                    onChange={(value) => handlePermissionChange(account.id, 'trading', value)}
                  />
                </div>
                
                <div className="flex justify-between items-center p-3 border border-gray-700 rounded-lg">
                  <div>
                    <p className="font-medium">Withdrawals</p>
                    <p className="text-sm text-gray-400">Allow fund withdrawals</p>
                  </div>
                  <Switch 
                    checked={account.permissions.withdrawals}
                    onChange={(value) => handlePermissionChange(account.id, 'withdrawals', value)}
                  />
                </div>
                
                <div className="flex justify-between items-center p-3 border border-gray-700 rounded-lg">
                  <div>
                    <p className="font-medium">Learning Materials</p>
                    <p className="text-sm text-gray-400">Access to educational content</p>
                  </div>
                  <Switch 
                    checked={account.permissions.learning}
                    onChange={(value) => handlePermissionChange(account.id, 'learning', value)}
                  />
                </div>
                
                <div className="flex justify-between items-center p-3 border border-gray-700 rounded-lg">
                  <div>
                    <p className="font-medium">Deposits</p>
                    <p className="text-sm text-gray-400">Allow adding funds to account</p>
                  </div>
                  <Switch 
                    checked={account.permissions.deposits}
                    onChange={(value) => handlePermissionChange(account.id, 'deposits', value)}
                  />
                </div>
                
                <div className="flex justify-between items-center p-3 border border-gray-700 rounded-lg">
                  <div>
                    <p className="font-medium">API Access</p>
                    <p className="text-sm text-gray-400">Allow use of API keys</p>
                  </div>
                  <Switch 
                    checked={account.permissions.apiAccess}
                    onChange={(value) => handlePermissionChange(account.id, 'apiAccess', value)}
                  />
                </div>
                
                <div className="flex justify-between items-center p-3 border border-gray-700 rounded-lg">
                  <div>
                    <p className="font-medium">Recurring Investments</p>
                    <p className="text-sm text-gray-400">Allow setting up recurring investments</p>
                  </div>
                  <Switch 
                    checked={account.permissions.recurringInvestments}
                    onChange={(value) => handlePermissionChange(account.id, 'recurringInvestments', value)}
                  />
                </div>
                
                <div className="flex justify-between items-center p-3 border border-gray-700 rounded-lg">
                  <div>
                    <p className="font-medium">Transfer Between Accounts</p>
                    <p className="text-sm text-gray-400">Allow moving funds between accounts</p>
                  </div>
                  <Switch 
                    checked={account.permissions.transferBetweenAccounts}
                    onChange={(value) => handlePermissionChange(account.id, 'transferBetweenAccounts', value)}
                  />
                </div>
                
                <div className="flex justify-between items-center p-3 border border-gray-700 rounded-lg">
                  <div>
                    <p className="font-medium">Advanced Orders</p>
                    <p className="text-sm text-gray-400">Allow limit, stop, and other order types</p>
                  </div>
                  <Switch 
                    checked={account.permissions.advancedOrders}
                    onChange={(value) => handlePermissionChange(account.id, 'advancedOrders', value)}
                  />
                </div>
              </div>
              
              {/* Age-based permissions warning */}
              {account.ageInYears < 13 && account.permissions.trading && (
                <div className="mt-4 p-3 bg-yellow-900/50 border border-yellow-600 rounded-lg">
                  <p className="text-yellow-300 font-medium">Trading Access Warning</p>
                  <p className="text-sm text-yellow-200">
                    This minor is under 13 years old. Consider adding additional oversight for trading activities.
                  </p>
                </div>
              )}
              
              {/* Pending changes indicator */}
              {Object.keys(pendingChanges[account.id] || {}).length > 0 && (
                <div className="mt-4 p-2 bg-blue-900/30 border border-blue-600 rounded-lg text-sm text-blue-300">
                  Unsaved changes will take effect after clicking "Save Changes"
                </div>
              )}
            </div>
          ))}
        </div>
      )}
      
      {/* Education reminder */}
      <div className="mt-8 bg-indigo-900/30 p-4 rounded-lg">
        <h3 className="text-lg font-semibold text-indigo-300">Educational Requirements</h3>
        <p className="text-sm text-indigo-200 mt-1">
          Minors may need to complete specific educational modules before certain permissions can be granted. 
          Check the Learning section to see available educational content.
        </p>
        <Button
          className="mt-3 bg-indigo-600 hover:bg-indigo-700 text-sm"
          onClick={() => window.location.href = '/learning'}
        >
          View Educational Content
        </Button>
      </div>
    </div>
  );
};

export default GuardianPermissions;