---
title: "Database Dictionary"
confidentiality: "PROPRIETARY & CONFIDENTIAL"
---

<!-- PROPRIETARY NOTICE
This document contains proprietary information of Elson Wealth Management Inc.
Unauthorized use, reproduction, or distribution is strictly prohibited.
Copyright © 2025 Elson Wealth Management Inc. All rights reserved.
-->

# Elson Wealth Trading Platform - Database Dictionary

This document provides a comprehensive overview of the database schema for the Elson Wealth Trading Platform. It includes tables, fields, data types, relationships, and purpose descriptions.

## Table of Contents

1. [Users and Authentication](#users-and-authentication)
2. [Accounts and Portfolios](#accounts-and-portfolios)
3. [Trading and Orders](#trading-and-orders)
4. [Micro-Investing](#micro-investing)
5. [Subscriptions and Payments](#subscriptions-and-payments)
6. [Notifications](#notifications)
7. [Educational Content](#educational-content)
8. [Enumerations](#enumerations)

## Users and Authentication

### Table: users

The core user table storing all account holders, including guardians and minors.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, NOT NULL | Unique identifier for the user |
| email | String | NOT NULL, UNIQUE | User's email address, used for login |
| username | String | NOT NULL, UNIQUE | User's chosen username |
| hashed_password | String | NOT NULL | Securely hashed password |
| full_name | String | NULL | User's full legal name |
| is_active | Boolean | DEFAULT TRUE | Whether the account is active |
| is_superuser | Boolean | DEFAULT FALSE | Whether user has administrative privileges |
| created_at | DateTime | NOT NULL | When the account was created |
| last_login | DateTime | NULL | When the user last logged in |
| role | Enum (user_role) | NOT NULL, DEFAULT 'adult' | User role: 'adult', 'minor', or 'admin' |
| birthdate | Date | NULL | User's date of birth, especially for minors |

**Indexes:**
- `ix_users_email` (email)
- `ix_users_username` (username)

### Table: user_settings

Contains user preferences, particularly for micro-investing features.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, NOT NULL | Unique identifier for the settings record |
| user_id | Integer | FK to users(id), UNIQUE | The user these settings belong to |
| micro_investing_enabled | Boolean | NULL | Whether micro-investing is enabled |
| roundup_enabled | Boolean | NULL | Whether purchase roundups are enabled |
| roundup_multiplier | Float | NULL | Multiplier applied to rounded-up amounts |
| roundup_frequency | Enum (roundupfrequency) | NULL | When to invest roundups ('daily', 'weekly', 'threshold') |
| roundup_threshold | Float | NULL | Minimum amount needed to trigger a threshold-based roundup |
| micro_invest_target_type | Enum (microinvesttarget) | NULL | Where to direct micro-investments |
| micro_invest_portfolio_id | Integer | FK to portfolios(id), NULL | Portfolio for micro-investments, if applicable |
| micro_invest_symbol | String(10) | NULL | Symbol to invest in if target is a specific security |
| bank_account_linked | Boolean | NULL | Whether user has linked a bank account |
| card_accounts_linked | Boolean | NULL | Whether user has linked card accounts for roundups |
| linked_accounts_data | JSON | NULL | Data about linked external accounts |
| notify_on_roundup | Boolean | NULL | Whether to notify about roundup investments |
| notify_on_investment | Boolean | NULL | Whether to notify about regular investments |
| max_weekly_roundup | Float | NULL | Maximum weekly amount from roundups |
| max_monthly_micro_invest | Float | NULL | Maximum monthly amount from micro-investing |
| completed_micro_invest_education | Boolean | NULL | Whether user completed micro-investing tutorial |
| created_at | DateTime | NULL | When settings were created |
| updated_at | DateTime | NULL | When settings were last updated |

**Indexes:**
- `ix_user_settings_id` (id)

## Accounts and Portfolios

### Table: accounts

Represents financial accounts that can hold portfolios, supporting custodial relationships.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, NOT NULL | Unique identifier for the account |
| user_id | Integer | FK to users(id), NOT NULL | User who owns this account |
| guardian_id | Integer | FK to users(id), NULL | Guardian user for custodial accounts |
| account_type | Enum (account_type) | NOT NULL, DEFAULT 'personal' | Type: 'personal' or 'custodial' |
| account_number | String | NOT NULL, UNIQUE | Unique account identifier |
| institution | String | NOT NULL | Financial institution holding the account |
| is_active | Boolean | DEFAULT TRUE | Whether the account is active |
| created_at | DateTime | DEFAULT NOW() | When the account was created |
| updated_at | DateTime | DEFAULT NOW(), ON UPDATE NOW() | When the account was last updated |

**Indexes:**
- `ix_accounts_account_number` (account_number, UNIQUE)

### Table: portfolios

Represents investment portfolios within accounts.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, NOT NULL | Unique identifier for the portfolio |
| user_id | Integer | FK to users(id), NOT NULL | User who owns this portfolio |
| account_id | Integer | FK to accounts(id), NULL | Account this portfolio belongs to |
| total_value | Numeric(18,8) | NOT NULL | Current total value of the portfolio |
| cash_balance | Numeric(18,8) | NOT NULL | Available cash in the portfolio |
| invested_amount | Numeric(18,8) | NOT NULL | Total amount invested in securities |
| positions | JSON | NULL | Detailed position data (may be legacy) |
| created_at | DateTime | NOT NULL | When the portfolio was created |
| updated_at | DateTime | NOT NULL | When the portfolio was last updated |
| risk_profile | String | DEFAULT 'moderate', NULL | Risk profile: 'conservative', 'moderate', 'aggressive', etc. |
| last_rebalanced_at | DateTime | NULL | When the portfolio was last rebalanced |

### Table: positions

Represents individual security positions within portfolios.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, NOT NULL | Unique identifier for the position |
| portfolio_id | Integer | FK to portfolios(id), NOT NULL | Portfolio this position belongs to |
| symbol | String(10) | NOT NULL | Security symbol (ticker) |
| quantity | Numeric(18,8) | NOT NULL | Quantity owned (supports fractional shares) |
| average_price | Numeric(18,8) | NOT NULL | Average acquisition price per share |
| current_price | Numeric(18,8) | NULL | Current market price per share |
| created_at | DateTime | NOT NULL | When the position was created |
| updated_at | DateTime | NOT NULL | When the position was last updated |

**Indexes:**
- `ix_positions_symbol` (symbol)

## Trading and Orders

### Table: trades

Records all trade orders, both pending and executed.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, NOT NULL | Unique identifier for the trade |
| user_id | Integer | FK to users(id), NOT NULL | User who placed the trade |
| symbol | String(10) | NOT NULL | Security symbol (ticker) |
| order_type | Enum (ordertype) | NOT NULL | Order type: 'market', 'limit' |
| side | String | NOT NULL | Buy or sell |
| quantity | Numeric(18,8) | NULL | Quantity to trade (can be null for dollar-based) |
| price | Numeric(18,8) | NULL | Execution price, if known |
| limit_price | Numeric(18,8) | NULL | Price limit for limit orders |
| stop_price | Numeric(18,8) | NULL | Trigger price for stop orders |
| status | Enum (trade_status) | NOT NULL, DEFAULT 'pending' | Current order status |
| filled_at | DateTime | NULL | When the order was filled (executed) |
| commission | Numeric(18,8) | NOT NULL | Trading commission charged |
| total_amount | Float | NULL | Total monetary value of the trade |
| external_order_id | String | NULL | ID from external broker system |
| created_at | DateTime | NOT NULL | When the order was created |
| updated_at | DateTime | NOT NULL | When the order was last updated |
| requested_by_user_id | Integer | FK to users(id), NULL | User who requested the trade (for custodial) |
| approved_by_user_id | Integer | FK to users(id), NULL | User who approved the trade (for custodial) |
| rejection_reason | Text | NULL | Reason if the trade was rejected |
| approved_at | DateTime | NULL | When the trade was approved |
| executed_at | DateTime | NULL | When the trade was executed |
| executed_by_user_id | Integer | FK to users(id), NULL | User who executed the trade (admin action) |
| is_fractional | Boolean | NULL | Whether this is a fractional share trade |
| investment_amount | Float | NULL | Dollar amount for dollar-based investing |
| investment_type | Enum (investmenttype) | NULL | Type of investment |
| trade_source | Enum (tradesource) | NULL | Source of the trade request |
| filled_quantity | Float | NULL | Actual executed quantity |
| filled_price | Float | NULL | Actual execution price |
| recurring_investment_id | Integer | FK to recurring_investments(id), NULL | Related recurring investment if applicable |
| metadata | JSON | NULL | Additional trade metadata |

**Indexes:**
- `ix_trades_symbol` (symbol)
- `ix_trades_created_at` (created_at)

### Table: recurring_investments

Represents scheduled recurring investment plans.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, NOT NULL | Unique identifier for the recurring investment |
| user_id | Integer | FK to users(id), NOT NULL | User who set up the investment |
| portfolio_id | Integer | FK to portfolios(id), NOT NULL | Target portfolio |
| symbol | String(20) | NOT NULL | Security symbol to invest in |
| investment_amount | Numeric(16,2) | NOT NULL | Amount to invest each period |
| frequency | Enum (recurringfrequency) | NOT NULL | How often to invest |
| start_date | DateTime | NOT NULL, DEFAULT NOW() | When to start the recurring investment |
| end_date | DateTime | NULL | When to end the recurring investment (if any) |
| next_investment_date | DateTime | NOT NULL | When the next investment will occur |
| last_execution_date | DateTime | NULL | When the last investment occurred |
| is_active | Boolean | NOT NULL, DEFAULT TRUE | Whether the plan is active |
| execution_count | Integer | NOT NULL, DEFAULT 0 | Number of times executed |
| description | Text | NULL | User-provided description |
| created_at | DateTime | NOT NULL, DEFAULT NOW() | When the plan was created |
| updated_at | DateTime | NOT NULL, DEFAULT NOW() | When the plan was last updated |
| metadata | JSON | NULL | Additional configuration metadata |

**Indexes:**
- `ix_recurring_investments_id` (id)

## Micro-Investing

### Table: roundup_transactions

Tracks transactions used for roundup micro-investing.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, NOT NULL | Unique identifier for the roundup record |
| user_id | Integer | FK to users(id), NULL | User whose transaction was rounded up |
| transaction_amount | Float | NOT NULL | Original transaction amount |
| roundup_amount | Float | NOT NULL | Amount rounded up (to be invested) |
| transaction_date | DateTime | NULL | When the original transaction occurred |
| description | String(255) | NULL | Description of the original transaction |
| source | String(50) | NULL | Source of the transaction |
| status | String(20) | NULL | Processing status of the roundup |
| invested_at | DateTime | NULL | When the roundup was invested |
| trade_id | Integer | FK to trades(id), NULL | Trade resulting from this roundup |

**Indexes:**
- `ix_roundup_transactions_id` (id)

## Subscriptions and Payments

### Table: subscriptions

Tracks user subscription plans.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, NOT NULL | Unique identifier for the subscription |
| user_id | Integer | FK to users(id), NOT NULL | User who owns the subscription |
| plan | Enum (subscriptionplan) | NOT NULL | Subscription tier: 'free', 'premium', 'family' |
| billing_cycle | Enum (billingcycle) | NOT NULL | Billing frequency: 'monthly', 'annually' |
| price | Float | NOT NULL | Subscription price per cycle |
| start_date | DateTime | NOT NULL | When the subscription began |
| end_date | DateTime | NULL | When the subscription ends/ended |
| auto_renew | Boolean | NOT NULL, DEFAULT TRUE | Whether to automatically renew |
| trial_end_date | DateTime | NULL | When the trial period ends/ended |
| payment_method_id | String | NULL | Payment method identifier |
| payment_method_type | Enum (paymentmethod) | NULL | Type of payment method |
| encrypted_payment_details | Text | NULL | Encrypted payment details |
| is_active | Boolean | NOT NULL, DEFAULT TRUE | Whether the subscription is active |
| canceled_at | DateTime | NULL | When the subscription was canceled |
| created_at | DateTime | NOT NULL, DEFAULT NOW() | When the subscription record was created |
| updated_at | DateTime | NOT NULL, DEFAULT NOW() | When the subscription was last updated |
| paypal_agreement_id | String | NULL | PayPal billing agreement ID |
| paypal_payer_id | String | NULL | PayPal payer ID |

**Indexes:**
- `ix_subscriptions_id` (id)
- `ix_subscriptions_user_id` (user_id)
- `ix_subscriptions_payment_method_id` (payment_method_id)
- `ix_subscriptions_plan` (plan)

### Table: subscription_payments

Records individual subscription payment transactions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, NOT NULL | Unique identifier for the payment |
| subscription_id | Integer | FK to subscriptions(id), NOT NULL | Related subscription |
| amount | Float | NOT NULL | Payment amount |
| status | Enum (paymentstatus) | NOT NULL | Payment status |
| payment_date | DateTime | NOT NULL, DEFAULT NOW() | When the payment was processed |
| provider_payment_id | String | NULL | Payment ID from payment provider |
| provider_payment_data | JSON | NULL | Detailed payment data from provider |
| created_at | DateTime | NOT NULL, DEFAULT NOW() | When the payment record was created |
| updated_at | DateTime | NOT NULL, DEFAULT NOW() | When the payment record was last updated |

**Indexes:**
- `ix_subscription_payments_id` (id)
- `ix_subscription_payments_subscription_id` (subscription_id)

### Table: subscription_history

Tracks changes to subscriptions for auditing purposes.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, NOT NULL | Unique identifier for the history record |
| subscription_id | Integer | FK to subscriptions(id), NOT NULL | Related subscription |
| change_type | String | NOT NULL | Type of change (upgrade, downgrade, etc.) |
| change_data | JSON | NULL | Detailed data about the change |
| changed_at | DateTime | NOT NULL | When the change occurred |

**Indexes:**
- `ix_subscription_history_subscription_id` (subscription_id)

## Notifications

### Table: notifications

Stores user notifications for various system events.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | String | PK, NOT NULL | Unique identifier for the notification |
| user_id | Integer | FK to users(id), NOT NULL | User this notification is for |
| type | String | NOT NULL | Notification type/category |
| message | Text | NOT NULL | Notification message content |
| requires_action | Boolean | NOT NULL, DEFAULT FALSE | Whether user action is required |
| is_read | Boolean | NOT NULL, DEFAULT FALSE | Whether notification has been read |
| timestamp | DateTime | NOT NULL, DEFAULT NOW() | When the notification was created |
| data | JSON | NULL | Additional notification data |
| minor_account_id | Integer | FK to accounts(id), NULL | Related custodial account, if applicable |
| trade_id | Integer | FK to trades(id), NULL | Related trade, if applicable |

**Indexes:**
- `ix_notifications_user_id` (user_id)
- `ix_notifications_timestamp` (timestamp)
- `ix_notifications_is_read` (is_read)

## Educational Content

Educational content tables were created in migration 20250310_add_educational_models.py.

## Enumerations

The database uses the following enumerated types:

### User and Account Related
- **user_role**: 'adult', 'minor', 'admin'
- **account_type**: 'personal', 'custodial'

### Trading Related
- **trade_status**: 'pending_approval', 'pending', 'filled', 'cancelled', 'rejected', 'expired'
- **ordertype**: 'market', 'limit'
- **tradesource**: 'user_initiated', 'recurring', 'rebalancing', 'dividend_reinvestment', 'aggregated'
- **investmenttype**: 'standard', 'dollar_based', 'micro', 'roundup'

### Micro-Investing Related
- **roundupfrequency**: 'daily', 'weekly', 'threshold'
- **microinvesttarget**: 'default_portfolio', 'specific_portfolio', 'specific_symbol', 'recommended_etf'
- **recurringfrequency**: 'daily', 'weekly', 'monthly', 'quarterly'

### Subscription Related
- **subscriptionplan**: 'free', 'premium', 'family'
- **billingcycle**: 'monthly', 'annually'
- **paymentstatus**: 'pending', 'succeeded', 'failed', 'refunded', 'canceled'
- **paymentmethod**: 'credit_card', 'bank_account', 'paypal', 'apple_pay', 'google_pay'

### Notification Related
- **notification_type**: 'trade_request', 'trade_executed', 'withdrawal', 'deposit', 'login', 'settings_change', 'request', 'trade_approved', 'trade_rejected', 'new_recommendation', 'portfolio_rebalance', 'account_linked', 'security_alert'

## Database Diagrams

### Core Entities
```
users 1──────┐
   │         │
   │         ▼
   │    accounts 1──────┐
   │         │          │
   │         │          │
   │         ▼          ▼
   └───► portfolios 1───┐
               │        │
               │        │
               ▼        │
           positions    │
                        │
                   trades
```

### Subscription Flow
```
users 1───► subscriptions 1───► subscription_payments
             │
             ▼
      subscription_history
```

### Micro-Investing Flow
```
users 1───► user_settings
   │         │
   │         ▼
   │    roundup_transactions ──► trades
   │
   └───► recurring_investments ──► trades
```

## Database Dialect Support

The database schema is designed to work with both PostgreSQL (production) and SQLite (development/testing). Key differences in implementation include:

- JSON data is stored as JSONB in PostgreSQL and as TEXT in SQLite
- Enum types are created as proper ENUM types in PostgreSQL and as string fields in SQLite
- Default values use different SQL syntax depending on the dialect

---

**© 2025 Elson Wealth Management Inc. All rights reserved.**