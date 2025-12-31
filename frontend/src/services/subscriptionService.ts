import api from './api';

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

export interface FeatureAccessResponse {
  feature: string;
  has_access: boolean;
  required_plan?: SubscriptionPlan;
}

export interface CancelSubscriptionParams {
  reason?: string;
  immediate: boolean;
}

export const subscriptionService = {
  async getActiveSubscription(): Promise<Subscription | null> {
    try {
      const response = await api.get('/subscriptions/active');
      return response.data || null;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  async getAllSubscriptions(): Promise<Subscription[]> {
    const response = await api.get('/subscriptions');
    return response.data;
  },

  async getSubscription(id: number): Promise<Subscription> {
    const response = await api.get(`/subscriptions/${id}`);
    return response.data;
  },

  async cancelSubscription(id: number, params: CancelSubscriptionParams): Promise<Subscription> {
    const response = await api.post(`/subscriptions/${id}/cancel`, params);
    return response.data;
  },

  async checkFeatureAccess(feature: string): Promise<FeatureAccessResponse> {
    const response = await api.post('/subscriptions/check-feature', { feature });
    return response.data;
  },

  getPlanDetails(plan: SubscriptionPlan, billingCycle: BillingCycle) {
    const pricing: Record<string, Record<string, number>> = {
      [SubscriptionPlan.PREMIUM]: {
        [BillingCycle.MONTHLY]: 9.99,
        [BillingCycle.ANNUALLY]: 95.88,
      },
      [SubscriptionPlan.FAMILY]: {
        [BillingCycle.MONTHLY]: 19.99,
        [BillingCycle.ANNUALLY]: 191.88,
      },
    };

    const features: Record<string, string[]> = {
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

export default subscriptionService;
