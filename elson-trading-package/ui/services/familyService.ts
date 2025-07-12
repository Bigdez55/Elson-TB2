import api, { handleApiError } from './api';
import { cacheManager } from '../utils/cacheUtils';

// Create a cache for family-related data
const familyCache = cacheManager.createCache('family', {
  ttl: 5 * 60 * 1000, // 5 minutes
  maxItems: 50
});

export interface MinorAccount {
  id: number;
  email: string;
  firstName: string;
  lastName: string;
  birthdate: string;
  guardianId: number;
  guardianName: string;
  accountId: number | null;
}

export interface MinorAccountWithPermissions extends MinorAccount {
  permissions: {
    trading: boolean;
    withdrawals: boolean;
    learning: boolean;
    deposits: boolean;
    apiAccess: boolean;
    recurringInvestments: boolean;
    transferBetweenAccounts: boolean;
    advancedOrders: boolean;
  };
  ageInYears: number;
}

export interface GuardianStatus {
  isGuardian: boolean;
  minorCount: number;
  totalTrades: number;
  pendingApprovals: number;
  twoFactorEnabled: boolean;
  requires2faSetup: boolean;
}

export interface PendingTrade {
  tradeId: number;
  minorId: number;
  minorName: string;
  symbol: string;
  quantity: number;
  price: number;
  tradeType: string;
  createdAt: string;
  status: string;
}

export interface Notification {
  id: string;
  minorAccountId: number;
  minorName: string;
  type: string;
  message: string;
  requiresAction: boolean;
  timestamp: string;
  isRead: boolean;
  tradeId?: number;
  symbol?: string;
  quantity?: number;
  price?: number;
  tradeType?: string;
}

export interface Permission {
  id: number;
  name: string;
  description?: string;
  permissionType: string;
  requiresGuardianApproval: boolean;
  minAge?: number;
  isGranted: boolean;
  grantedAt?: string;
}

export const FamilyService = {
  /**
   * Get all minor accounts for the guardian
   */
  getMinorAccounts: async (forceRefresh = false): Promise<MinorAccount[]> => {
    try {
      const cachedData = familyCache.get('minorAccounts');
      if (cachedData && !forceRefresh) {
        return cachedData;
      }

      const response = await api.get('/family/minors');
      const minorAccounts = response.data;
      
      familyCache.set('minorAccounts', minorAccounts);
      return minorAccounts;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Create a new minor account
   */
  createMinorAccount: async (minorData: {
    email: string;
    firstName: string;
    lastName: string;
    birthdate: string;
  }): Promise<MinorAccount> => {
    try {
      const response = await api.post('/family/minor', {
        email: minorData.email,
        first_name: minorData.firstName,
        last_name: minorData.lastName,
        birthdate: minorData.birthdate
      });
      
      // Invalidate cache
      familyCache.invalidate('minorAccounts');
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Get guardian status
   */
  getGuardianStatus: async (forceRefresh = false): Promise<GuardianStatus> => {
    try {
      const cachedData = familyCache.get('guardianStatus');
      if (cachedData && !forceRefresh) {
        return cachedData;
      }

      const response = await api.get('/family/guardian/status');
      const guardianStatus = response.data;
      
      familyCache.set('guardianStatus', guardianStatus);
      return guardianStatus;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Get pending trades requiring guardian approval
   */
  getPendingTrades: async (forceRefresh = false): Promise<PendingTrade[]> => {
    try {
      const cachedData = familyCache.get('pendingTrades');
      if (cachedData && !forceRefresh) {
        return cachedData;
      }

      const response = await api.get('/family/trades/pending');
      const pendingTrades = response.data;
      
      familyCache.set('pendingTrades', pendingTrades);
      return pendingTrades;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Approve or reject a minor's trade
   */
  approveMinorTrade: async (tradeId: number, approved: boolean, rejectionReason?: string): Promise<PendingTrade> => {
    try {
      const response = await api.post(`/family/trade/${tradeId}/approve`, {
        approved,
        rejection_reason: rejectionReason
      });
      
      // Invalidate cache
      familyCache.invalidate('pendingTrades');
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Get guardian notifications
   */
  getNotifications: async (options: {
    unreadOnly?: boolean;
    minorAccountId?: number;
    limit?: number;
    forceRefresh?: boolean;
  } = {}): Promise<Notification[]> => {
    try {
      const { unreadOnly = false, minorAccountId, limit = 50, forceRefresh = false } = options;
      
      // Create a cache key that includes the filter parameters
      const cacheKey = `notifications-${unreadOnly}-${minorAccountId || 'all'}-${limit}`;
      
      const cachedData = familyCache.get(cacheKey);
      if (cachedData && !forceRefresh) {
        return cachedData;
      }

      // Build query parameters
      const params: Record<string, any> = {
        unread_only: unreadOnly,
        limit
      };
      
      if (minorAccountId) {
        params.min_account_id = minorAccountId;
      }

      const response = await api.get('/family/notifications', { params });
      const notifications = response.data;
      
      // Convert snake_case to camelCase
      const formattedNotifications = notifications.map((notification: any) => ({
        id: notification.id,
        minorAccountId: notification.minor_account_id,
        minorName: notification.minor_name,
        type: notification.type,
        message: notification.message,
        requiresAction: notification.requires_action,
        timestamp: notification.timestamp,
        isRead: notification.is_read,
        tradeId: notification.trade_id,
        symbol: notification.symbol,
        quantity: notification.quantity,
        price: notification.price,
        tradeType: notification.trade_type
      }));
      
      familyCache.set(cacheKey, formattedNotifications);
      return formattedNotifications;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Mark notification as read
   */
  markNotificationAsRead: async (notificationId: string): Promise<void> => {
    try {
      await api.post(`/family/notifications/${notificationId}/read`);
      
      // Invalidate notifications cache
      familyCache.invalidateByPrefix('notifications');
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Get minor accounts with permissions
   */
  getMinorAccountsWithPermissions: async (forceRefresh = false): Promise<MinorAccountWithPermissions[]> => {
    try {
      const cacheKey = 'minorAccountsWithPermissions';
      const cachedData = familyCache.get(cacheKey);
      if (cachedData && !forceRefresh) {
        return cachedData;
      }

      // First get the minor accounts
      const minorAccounts = await FamilyService.getMinorAccounts(forceRefresh);
      
      // Then for each account, get their permissions
      const accountsWithPermissions: MinorAccountWithPermissions[] = await Promise.all(
        minorAccounts.map(async (account) => {
          // Calculate age from birthdate
          const birthdate = new Date(account.birthdate);
          const today = new Date();
          const ageInYears = today.getFullYear() - birthdate.getFullYear() - 
            (today.getMonth() < birthdate.getMonth() || 
            (today.getMonth() === birthdate.getMonth() && today.getDate() < birthdate.getDate()) ? 1 : 0);
          
          // Get permissions from API
          let permissions = {
            trading: false,
            withdrawals: false,
            learning: true, // Learning is enabled by default
            deposits: true, // Deposits are enabled by default
            apiAccess: false,
            recurringInvestments: false,
            transferBetweenAccounts: false,
            advancedOrders: false
          };
          
          try {
            // Get permissions from API
            const response = await api.get(`/family/minors/${account.id}/permissions`);
            
            // Map the permission types to our schema
            if (response.data) {
              const permissionsData = response.data;
              
              permissions = {
                trading: permissionsData.trading || false,
                withdrawals: permissionsData.withdrawals || false,
                learning: permissionsData.learning !== false, // Default to true
                deposits: permissionsData.deposits !== false, // Default to true
                apiAccess: permissionsData.apiAccess || false,
                recurringInvestments: permissionsData.recurringInvestments || false,
                transferBetweenAccounts: permissionsData.transferBetweenAccounts || false,
                advancedOrders: permissionsData.advancedOrders || false
              };
            }
          } catch (error) {
            console.error(`Error fetching permissions for minor ${account.id}:`, error);
            // Fall back to default permissions
          }

          return {
            ...account,
            permissions,
            ageInYears
          };
        })
      );
      
      familyCache.set(cacheKey, accountsWithPermissions);
      return accountsWithPermissions;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Update minor account permissions
   */
  updateMinorPermissions: async (
    minorId: number, 
    permissions: {
      trading?: boolean;
      withdrawals?: boolean;
      learning?: boolean;
      deposits?: boolean;
      apiAccess?: boolean;
      recurringInvestments?: boolean;
      transferBetweenAccounts?: boolean;
      advancedOrders?: boolean;
    }
  ): Promise<void> => {
    try {
      await api.put(`/family/minors/${minorId}/permissions`, permissions);
      
      // Invalidate cache
      familyCache.invalidate('minorAccountsWithPermissions');
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Get all available trading permissions
   */
  getTradingPermissions: async (forceRefresh = false): Promise<Permission[]> => {
    try {
      const cacheKey = 'tradingPermissions';
      const cachedData = familyCache.get(cacheKey);
      if (cachedData && !forceRefresh) {
        return cachedData;
      }

      const response = await api.get('/education/permissions/trading');
      const permissions = response.data;
      
      familyCache.set(cacheKey, permissions);
      return permissions;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Get user permissions for a minor
   */
  getMinorPermissions: async (minorId: number, forceRefresh = false): Promise<Permission[]> => {
    try {
      const cacheKey = `minorPermissions-${minorId}`;
      const cachedData = familyCache.get(cacheKey);
      if (cachedData && !forceRefresh) {
        return cachedData;
      }

      const response = await api.get(`/education/permissions/minors/${minorId}`);
      const permissions = response.data;
      
      familyCache.set(cacheKey, permissions);
      return permissions;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Grant permission to a minor
   */
  grantMinorPermission: async (minorId: number, permissionId: number, overrideReason?: string): Promise<void> => {
    try {
      await api.post(
        `/education/permissions/minors/${minorId}/grant/${permissionId}`,
        { override_reason: overrideReason }
      );
      
      // Invalidate cache
      familyCache.invalidate(`minorPermissions-${minorId}`);
      familyCache.invalidate('minorAccountsWithPermissions');
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Revoke permission from a minor
   */
  revokeMinorPermission: async (minorId: number, permissionId: number): Promise<void> => {
    try {
      await api.post(`/education/permissions/minors/${minorId}/revoke/${permissionId}`);
      
      // Invalidate cache
      familyCache.invalidate(`minorPermissions-${minorId}`);
      familyCache.invalidate('minorAccountsWithPermissions');
    } catch (error) {
      throw handleApiError(error);
    }
  }
};

export default FamilyService;