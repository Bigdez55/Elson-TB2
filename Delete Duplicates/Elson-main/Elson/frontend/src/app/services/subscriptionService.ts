import api, { handleApiError } from './api';
import { generateCacheKey } from '../utils/cacheUtils';

// Create a dedicated subscription cache
import { CacheManager } from '../utils/cacheUtils';
const subscriptionCache = new CacheManager<any>({
  namespace: 'elson_subscription',
  defaultTTL: 5 * 60 * 1000, // 5 minutes
  maxSize: 20
});

export enum SubscriptionPlan {
  FREE = "free",
  PREMIUM = "premium",
  FAMILY = "family"
}

export enum BillingCycle {
  MONTHLY = "monthly",
  ANNUALLY = "annually"
}

export enum PaymentMethod {
  CREDIT_CARD = "credit_card",
  BANK_ACCOUNT = "bank_account",
  PAYPAL = "paypal",
  APPLE_PAY = "apple_pay",
  GOOGLE_PAY = "google_pay"
}

export interface CreditCardInfo {
  card_number: string;
  expiry_month: number;
  expiry_year: number;
  cvc: string;
  cardholder_name: string;
  billing_address?: {
    street: string;
    city: string;
    state: string;
    zip: string;
    country: string;
  };
}

export interface BankAccountInfo {
  account_number: string;
  routing_number: string;
  account_type: string;
  account_holder_name: string;
}

export interface PaymentMethodCreate {
  type: PaymentMethod;
  credit_card?: CreditCardInfo;
  bank_account?: BankAccountInfo;
  save_for_future: boolean;
}

export interface Subscription {
  id: number;
  user_id: number;
  plan: SubscriptionPlan;
  billing_cycle: BillingCycle;
  price: number;
  auto_renew: boolean;
  start_date: string;
  end_date?: string;
  trial_end_date?: string;
  payment_method_id?: string;
  payment_method_type?: PaymentMethod;
  is_active: boolean;
  canceled_at?: string;
  created_at: string;
  updated_at: string;
  status: string;
}

export interface SubscribeParams {
  plan: SubscriptionPlan;
  billing_cycle: BillingCycle;
  price: number;
  auto_renew: boolean;
  payment_method: PaymentMethodCreate;
  trial_days?: number;
}

export interface CancelSubscriptionParams {
  reason?: string;
  immediate: boolean;
}

export interface ChangePlanParams {
  new_plan: SubscriptionPlan;
  new_billing_cycle?: BillingCycle;
  prorate: boolean;
}

export interface FeatureAccessResponse {
  feature: string;
  has_access: boolean;
  required_plan?: SubscriptionPlan;
}

export const subscriptionService = {
  // Get active subscription
  async getActiveSubscription(forceRefresh: boolean = false): Promise<Subscription | null> {
    try {
      const cacheKey = generateCacheKey('active_subscription');
      
      // Check cache first if not forcing refresh
      if (!forceRefresh) {
        const cachedData = subscriptionCache.get(cacheKey);
        if (cachedData !== undefined) {
          return cachedData;
        }
      }
      
      // If not in cache or force refresh, fetch from API
      const response = await api.get('/api/v1/subscriptions/active');
      const data = response.data || null;
      
      // Cache the response data (even if null)
      subscriptionCache.set(cacheKey, data);
      
      return data;
    } catch (error) {
      if (error.response && error.response.status === 404) {
        // Cache the null result for "not found" responses
        subscriptionCache.set(generateCacheKey('active_subscription'), null);
        return null;
      }
      throw handleApiError(error);
    }
  },
  
  // Get all subscriptions
  async getAllSubscriptions(forceRefresh: boolean = false): Promise<Subscription[]> {
    try {
      const cacheKey = generateCacheKey('all_subscriptions');
      
      // Check cache first if not forcing refresh
      if (!forceRefresh) {
        const cachedData = subscriptionCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      // If not in cache or force refresh, fetch from API
      const response = await api.get('/api/v1/subscriptions');
      
      // Cache the response data
      subscriptionCache.set(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  // Get subscription by ID
  async getSubscription(id: number, forceRefresh: boolean = false): Promise<Subscription> {
    try {
      const cacheKey = generateCacheKey(`subscription_${id}`);
      
      // Check cache first if not forcing refresh
      if (!forceRefresh) {
        const cachedData = subscriptionCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      // If not in cache or force refresh, fetch from API
      const response = await api.get(`/api/v1/subscriptions/${id}`);
      
      // Cache the response data
      subscriptionCache.set(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  // Subscribe to a plan
  async subscribe(params: SubscribeParams): Promise<Subscription> {
    try {
      const response = await api.post('/api/v1/subscriptions/subscribe', params);
      
      // Clear subscription cache since we have a new subscription
      const activeCacheKey = generateCacheKey('active_subscription');
      const allCacheKey = generateCacheKey('all_subscriptions');
      subscriptionCache.remove(activeCacheKey);
      subscriptionCache.remove(allCacheKey);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  // Cancel subscription
  async cancelSubscription(id: number, params: CancelSubscriptionParams): Promise<Subscription> {
    try {
      const response = await api.post(`/api/v1/subscriptions/${id}/cancel`, params);
      
      // Clear subscription cache since we modified a subscription
      const activeCacheKey = generateCacheKey('active_subscription');
      const allCacheKey = generateCacheKey('all_subscriptions');
      const subscriptionCacheKey = generateCacheKey(`subscription_${id}`);
      
      subscriptionCache.remove(activeCacheKey);
      subscriptionCache.remove(allCacheKey);
      subscriptionCache.remove(subscriptionCacheKey);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  // Change subscription plan
  async changePlan(id: number, params: ChangePlanParams): Promise<Subscription> {
    try {
      const response = await api.post(`/api/v1/subscriptions/${id}/change-plan`, params);
      
      // Clear subscription cache since we modified a subscription
      const activeCacheKey = generateCacheKey('active_subscription');
      const allCacheKey = generateCacheKey('all_subscriptions');
      const subscriptionCacheKey = generateCacheKey(`subscription_${id}`);
      
      subscriptionCache.remove(activeCacheKey);
      subscriptionCache.remove(allCacheKey);
      subscriptionCache.remove(subscriptionCacheKey);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  // Verify bank account with micro-deposits
  async verifyBankAccount(
    subscriptionId: number, 
    amounts: number[], 
    bankAccountId?: string
  ): Promise<{ success: boolean; message: string; }> {
    try {
      const response = await api.post(`/api/v1/subscriptions/${subscriptionId}/verify-bank-account`, {
        amounts,
        bank_account_id: bankAccountId
      });
      return { success: true, message: 'Bank account verified successfully' };
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || 'Failed to verify bank account' 
      };
    }
  },
  
  // Check feature access
  async checkFeatureAccess(feature: string, forceRefresh: boolean = false): Promise<FeatureAccessResponse> {
    try {
      const cacheKey = generateCacheKey(`feature_access_${feature}`);
      
      // Check cache first if not forcing refresh
      if (!forceRefresh) {
        const cachedData = subscriptionCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      // If not in cache or force refresh, fetch from API
      const response = await api.post('/api/v1/subscriptions/check-feature', { feature });
      
      // Cache the response data
      subscriptionCache.set(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  // Cancel a pending subscription (used when PayPal payment is canceled)
  async cancelPendingSubscription(id: number): Promise<void> {
    try {
      // Use immediate cancellation for pending subscriptions
      await this.cancelSubscription(id, { immediate: true });
      
      // The cancelSubscription method already clears the cache
    } catch (error) {
      console.error("Error canceling pending subscription:", error);
      // Don't throw the error since this is a cleanup operation
      // and we don't want to block the user flow if it fails
      
      // Clear cache anyway in case the error is transient
      const activeCacheKey = generateCacheKey('active_subscription');
      const allCacheKey = generateCacheKey('all_subscriptions');
      const subscriptionCacheKey = generateCacheKey(`subscription_${id}`);
      
      subscriptionCache.remove(activeCacheKey);
      subscriptionCache.remove(allCacheKey);
      subscriptionCache.remove(subscriptionCacheKey);
    }
  },
  
  // Get plan details
  getPlanDetails(plan: SubscriptionPlan, billingCycle: BillingCycle) {
    const pricing = {
      [SubscriptionPlan.PREMIUM]: {
        [BillingCycle.MONTHLY]: 9.99,
        [BillingCycle.ANNUALLY]: 95.88, // 7.99/month
      },
      [SubscriptionPlan.FAMILY]: {
        [BillingCycle.MONTHLY]: 19.99,
        [BillingCycle.ANNUALLY]: 191.88, // 15.99/month
      },
    };
    
    const features = {
      [SubscriptionPlan.FREE]: [
        'Commission-free trading',
        'Basic market data',
        'Paper trading',
        'Basic educational content',
        'Portfolio tracking',
      ],
      [SubscriptionPlan.PREMIUM]: [
        'Everything in Free plan',
        'Unlimited recurring investments',
        'Advanced market data',
        'AI trading recommendations',
        'Tax-loss harvesting',
        'High-yield savings (5.00% APY)',
      ],
      [SubscriptionPlan.FAMILY]: [
        'Everything in Premium plan',
        'Up to 5 custodial accounts',
        'Family investment challenges',
        'Age-appropriate educational content',
        'Guardian approval workflow',
        'Multiple retirement accounts',
      ],
    };
    
    return {
      price: pricing[plan]?.[billingCycle] || 0,
      features: features[plan] || [],
      billingCycle,
      plan,
    };
  }
};