---
title: "Database Schema"
confidentiality: "PROPRIETARY & CONFIDENTIAL"
---

<\!-- PROPRIETARY NOTICE
This document contains proprietary information of Elson Wealth Management Inc.
Unauthorized use, reproduction, or distribution is strictly prohibited.
Copyright © 2025 Elson Wealth Management Inc. All rights reserved.
-->

# Elson Wealth + Trading Database Schema

This document describes the database schema for the Elson wealth management and trading platform.

## Overview

Elson uses PostgreSQL as its primary database. The schema is designed to efficiently support family account management, guardian-minor relationships, portfolio management, AI-powered trade execution, and market data analysis.

## Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    User     │       │  Portfolio  │       │    Trade    │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id          │       │ id          │       │ id          │
│ email       │◄──┐   │ name        │   ┌──►│ portfolio_id│
│ full_name   │   │   │ description │   │   │ symbol      │
│ password    │   │   │ user_id     │───┘   │ side        │
│ role        │   │   │ account_id  │       │ quantity    │
│ birthdate   │   │   │ created_at  │       │ price       │
│ is_active   │   └───│ updated_at  │       │ type        │
│ created_at  │       │ cash_balance│       │ status      │
│ updated_at  │       │ risk_profile│       │ requested_by│
└─────────────┘       └─────────────┘       │ approved_by │
      ▲   ▲                                 │ approved_at │
      │   │                                 │ created_at  │
      │   │                                 │ updated_at  │
      │   │                                 │ notes       │
      │   │                                 └─────────────┘
      │   │                                        │
      │   │                                        │
┌─────┴───┴───┐                            ┌───────▼───────┐
│   Account   │                            │ TradeExecution │
├─────────────┤                            ├───────────────┤
│ id          │                            │ id            │
│ user_id     │                            │ trade_id      │
│ guardian_id │◄────────────────┐          │ execution_time│
│ type        │                 │          │ filled_price  │
│ account_num │                 │          │ filled_quantity
│ institution │                 │          │ commission    │
│ is_active   │                 │          │ broker_trade_id
│ created_at  │                 │          └───────────────┘
│ updated_at  │                 │
└─────────────┘                 │          ┌───────────────┐
                                │          │Recommendation │
┌──────────────────┐            │          ├───────────────┤
│ QuantumModel     │            │          │ id            │
├──────────────────┤            │          │ user_id       │
│ id               │            │          │ symbol        │
│ name             │            │          │ action        │
│ description      │            │          │ quantity      │
│ model_type       │            │          │ price         │
│ hyperparameters  │            │          │ confidence    │
│ accuracy         │            │          │ strategy      │
│ created_at       │            │          │ reason        │
│ updated_at       │            │          │ timestamp     │
└──────────────────┘            │          └───────────────┘
                                │
┌──────────────────┐            │          ┌───────────────┐
│ Notification     │            │          │ RiskControl   │
├──────────────────┤            │          ├───────────────┤
│ id               │            │          │ id            │
│ user_id          │            │          │ user_id       │
│ type             │            │          │ guardian_id   │◄─┘
│ title            │            └──────────┤ max_position  │
│ message          │                       │ allowed_symbols
│ data             │                       │ is_active     │
│ is_read          │                       │ created_at    │
│ created_at       │                       │ updated_at    │
└──────────────────┘                       └───────────────┘
```

## Tables

### User

Stores user account information.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| email | VARCHAR(255) | User's email address (unique) |
| first_name | VARCHAR(255) | User's first name |
| last_name | VARCHAR(255) | User's last name |
| role | ENUM | 'adult', 'minor', or 'admin' |
| birthdate | DATE | User's birthdate (required for minors) |
| password | VARCHAR(255) | Hashed password |
| is_active | BOOLEAN | Account status |
| is_superuser | BOOLEAN | Admin privileges flag |
| created_at | TIMESTAMP | Account creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |
| last_login | TIMESTAMP | Last login timestamp |

### Portfolio

Represents a user's investment portfolio.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Foreign key to User |
| account_id | UUID | Foreign key to Account (optional) |
| total_value | DECIMAL(18,2) | Total portfolio value |
| cash_balance | DECIMAL(18,2) | Available cash in portfolio |
| invested_amount | DECIMAL(18,2) | Amount invested in securities |
| positions | JSONB | JSON representation of positions |
| risk_profile | VARCHAR(50) | 'conservative', 'moderate', or 'aggressive' |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |
| last_rebalanced_at | TIMESTAMP | Last portfolio rebalance timestamp |

### Account

Represents a brokerage account, which may be personal or custodial.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Foreign key to User (account owner) |
| guardian_id | UUID | Foreign key to User (guardian, for custodial accounts) |
| account_type | ENUM | 'personal' or 'custodial' |
| account_number | VARCHAR(50) | Brokerage account number |
| institution | VARCHAR(100) | Financial institution name |
| is_active | BOOLEAN | Account status |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

### Trade

Records of trade orders.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Foreign key to User |
| portfolio_id | UUID | Foreign key to Portfolio |
| symbol | VARCHAR(10) | Stock symbol |
| quantity | DECIMAL(18,6) | Number of shares |
| price | DECIMAL(18,2) | Price per share |
| trade_type | VARCHAR(10) | 'buy' or 'sell' |
| order_type | ENUM | 'market', 'limit', 'stop', 'stop_limit' |
| status | ENUM | 'pending_approval', 'pending', 'filled', 'cancelled', 'rejected', 'expired' |
| total_amount | DECIMAL(18,2) | Total transaction amount |
| requested_by_user_id | UUID | Foreign key to User (who requested the trade) |
| approved_by_user_id | UUID | Foreign key to User (who approved the trade) |
| rejection_reason | TEXT | Reason for rejection (if applicable) |
| created_at | TIMESTAMP | Order creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |
| approved_at | TIMESTAMP | Approval timestamp |
| executed_at | TIMESTAMP | Execution timestamp |

### TradeExecution

Details of executed trades.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| trade_id | UUID | Foreign key to Trade |
| execution_time | TIMESTAMP | When the trade executed |
| filled_price | DECIMAL(18,2) | Actual execution price |
| filled_quantity | INTEGER | Actual quantity filled |
| commission | DECIMAL(10,2) | Trading fee |
| broker_trade_id | VARCHAR(255) | ID from broker system |

### QuantumModel

Machine learning models for market prediction.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR(255) | Model name |
| description | TEXT | Model description |
| model_type | VARCHAR(50) | Classification, regression, etc. |
| hyperparameters | JSONB | Model parameters |
| accuracy | DECIMAL(5,2) | Model accuracy metric |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

### Recommendation

AI-generated investment recommendations.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Foreign key to User |
| symbol | VARCHAR(10) | Stock symbol |
| action | VARCHAR(10) | 'buy' or 'sell' |
| quantity | DECIMAL(18,6) | Recommended number of shares |
| price | DECIMAL(18,2) | Recommended price |
| confidence | DECIMAL(5,4) | Confidence score (0-1) |
| strategy | VARCHAR(50) | Name of strategy that generated recommendation |
| reason | TEXT | Explanation of recommendation |
| timestamp | TIMESTAMP | When recommendation was generated |

### Notification

System notifications for users.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Foreign key to User |
| type | VARCHAR(50) | Notification type |
| title | VARCHAR(255) | Notification title |
| message | TEXT | Notification content |
| data | JSONB | Additional structured data |
| is_read | BOOLEAN | Whether notification has been read |
| created_at | TIMESTAMP | Creation timestamp |

## Indexes

- `user_email_idx` on `User.email`
- `portfolio_user_id_idx` on `Portfolio.user_id`
- `portfolio_account_id_idx` on `Portfolio.account_id`
- `account_user_id_idx` on `Account.user_id`
- `account_guardian_id_idx` on `Account.guardian_id`
- `trade_portfolio_id_idx` on `Trade.portfolio_id`
- `trade_user_id_idx` on `Trade.user_id`
- `trade_symbol_idx` on `Trade.symbol`
- `trade_status_idx` on `Trade.status`
- `trade_requested_by_idx` on `Trade.requested_by_user_id`
- `trade_approved_by_idx` on `Trade.approved_by_user_id`
- `trade_execution_trade_id_idx` on `TradeExecution.trade_id`
- `recommendation_user_id_idx` on `Recommendation.user_id`
- `notification_user_id_idx` on `Notification.user_id`

## Constraints

- Foreign key constraints on all relations
- Unique constraint on `User.email`
- Unique constraint on `Account.account_number`
- Check constraints:
  - `User.role` in ('adult', 'minor', 'admin')
  - `Account.account_type` in ('personal', 'custodial')
  - `Trade.trade_type` in ('buy', 'sell')
  - `Trade.order_type` in ('market', 'limit', 'stop', 'stop_limit')
  - `Trade.status` in ('pending_approval', 'pending', 'filled', 'cancelled', 'rejected', 'expired')
  - `Portfolio.risk_profile` in ('conservative', 'moderate', 'aggressive')
  - `Recommendation.confidence` between 0 and 1

## Migrations

Database migrations are managed using Alembic. Key migration scripts include:

- `20240110_initial_migration.py` - Initial schema setup
- `20240229_add_custodial_accounts.py` - Adds family account management features including:
  - User role support (adult, minor, admin)
  - Custodial account relationships
  - Trade approval workflow
  - AI recommendation storage

## Data Archiving

Historical trade data older than one year is archived to separate tables for performance optimization while maintaining data accessibility for analysis.

## Security Considerations

- Guardian-minor relationships are enforced at the database level with referential integrity
- Trade approval workflow ensures minors cannot execute trades without guardian approval
- Authorization checks prevent unauthorized access to account data
- Sensitive data like account numbers is encrypted at rest

## Performance Considerations

- Partitioning is used for the `Trade` table (by month) to improve query performance
- Regular database maintenance includes index optimization and vacuuming
- Notification queries are optimized for real-time alerts
- Guardian approval workflows are designed for minimal latency
- AI recommendation queries are optimized for fast retrieval