# Elson Subscription Management System

## Overview

The Subscription Management System provides comprehensive subscription functionality for the Elson Wealth platform. It enables users to subscribe to different tiers of service, manage their payment methods, and upgrade or downgrade their subscriptions.

## Features

- Three subscription tiers: Free, Premium, and Family
- Monthly and annual billing cycles with proration support
- Secure payment processing with AES-256 encryption
- Automatic renewals with failure handling
- Comprehensive webhook integration with Stripe
- Feature access control based on subscription tier
- Trial periods with configurable durations
- Analytics for subscription metrics
- Token-based security with refresh token rotation

## Architecture

### Database Models

- `Subscription`: Stores subscription details (plan, billing cycle, pricing, renewal settings)
- `SubscriptionPayment`: Tracks payment history for subscriptions

### Service Layer

- `SubscriptionService`: Business logic for subscription operations
- `StripeService`: Dedicated service for Stripe API interactions
- `SubscriptionMetricsService`: Subscription analytics and reporting
- AES-256 encryption for sensitive payment details
- Configurable Stripe price IDs via application settings

### API Endpoints

- `GET /api/v1/subscriptions/`: List user subscriptions
- `GET /api/v1/subscriptions/active`: Get current active subscription
- `GET /api/v1/subscriptions/{id}`: Get subscription details
- `POST /api/v1/subscriptions/`: Create subscription (admin only)
- `POST /api/v1/subscriptions/subscribe`: Subscribe with payment information
- `PUT /api/v1/subscriptions/{id}`: Update subscription (admin only)
- `POST /api/v1/subscriptions/{id}/cancel`: Cancel subscription
- `POST /api/v1/subscriptions/{id}/change-plan`: Change subscription plan
- `POST /api/v1/subscriptions/check-feature`: Check feature access

## Subscription Tiers

### Free Tier
- Basic trading functionality
- Paper trading
- Basic educational content
- Limited portfolio tracking
- Basic market data

### Premium Tier ($9.99/month or $95.88/year)
- Advanced trading (limit orders, etc.)
- Fractional shares trading
- AI-powered recommendations
- Unlimited recurring investments
- Tax loss harvesting
- Advanced educational content
- Advanced market data
- High-yield savings account
- API access

### Family Tier ($19.99/month or $191.88/year)
- All Premium features
- Custodial accounts for children
- Guardian approval workflow
- Family challenges and goals
- Educational games for children
- Multiple retirement accounts

## Payment Processing

The system is fully integrated with Stripe for payment processing. To configure:

1. Set the `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET`, and `STRIPE_PUBLIC_KEY` in your environment
2. Configure the `STRIPE_PRICE_IDS` in `app/core/config.py` with your actual Stripe price IDs

The system handles the following Stripe interactions:
- Creating customers in Stripe
- Managing payment methods (credit cards, bank accounts)
- Processing subscription creation and updates
- Handling webhooks for subscription lifecycle events
- Managing invoice payments and failures

### Webhook Events
The system handles these Stripe webhook events:
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.paid`
- `invoice.payment_failed`
- `payment_method.attached`
- `payment_method.updated`

## Renewal Process

The renewal process is handled by a scheduled script (`process_subscription_renewals.py`) that should be run daily. It:

1. Identifies subscriptions due for renewal
2. Processes payments for renewals through Stripe API
3. Updates subscription end dates based on billing cycle
4. Handles payment failures with proper retry logic
5. Tracks payment history for audit purposes
6. Sends notifications for upcoming renewals and payment failures

The renewal system supports calendar-aware date calculations to handle varying month lengths and leap years.

## Feature Access Control

The `SubscriptionService.check_feature_access()` method controls access to premium features based on a user's subscription tier. This can be called from any API endpoint to verify access permissions.

## Security

- Payment details are encrypted using AES-256 before storage
- Only the last 4 digits of credit card/bank account numbers are stored
- All subscription API endpoints are protected by authentication with refresh token system
- Tokens include proper typing and validation to prevent misuse
- Session rotation on critical actions like logout and subscription changes
- Webhook signatures verified to prevent request forgery
- Users can only access their own subscription data (unless admin)
- Token revocation on logout for enhanced security

## Future Improvements

- Add support for coupons and promotional codes
- Enhance subscription usage analytics
- Add support for family member invitations
- Implement subscription-based rate limiting for API endpoints
- Support additional payment methods (Apple Pay, Google Pay)
- Create dashboard for subscription management
- Implement subscription gift cards