---
title: "Data Model"
confidentiality: "PROPRIETARY & CONFIDENTIAL"
---

<\!-- PROPRIETARY NOTICE
This document contains proprietary information of Elson Wealth Management Inc.
Unauthorized use, reproduction, or distribution is strictly prohibited.
Copyright © 2025 Elson Wealth Management Inc. All rights reserved.
-->

# Elson Wealth Trading Platform - Data Model

This document describes the data model for the Elson Wealth Trading Platform, including key entities, relationships, and database schema.

## Entity Relationship Diagram

```
┌───────────────┐      ┌────────────────┐       ┌───────────────┐
│               │      │                │       │               │
│     User      │──┐   │   Portfolio    │───┐   │   Position    │
│               │  │   │                │   │   │               │
└───────────────┘  │   └────────────────┘   │   └───────────────┘
                   │                        │
                   │   ┌────────────────┐   │   ┌───────────────┐
                   └──►│  Relationship  │   └──►│     Trade     │
                       │                │       │               │
                       └────────────────┘       └───────────────┘
                            │
                            │     ┌────────────────┐
                            └────►│  Notification  │
                                  │                │
                                  └────────────────┘
```

## Core Entities

### User

The User entity represents individuals using the platform, including regular users, guardians, and minors.

**Table: `users`**

| Column Name          | Type            | Description                               |
|----------------------|-----------------|-------------------------------------------|
| id                   | UUID            | Primary key                               |
| email                | VARCHAR(255)    | User's email address (unique)             |
| password_hash        | VARCHAR(255)    | Hashed password                           |
| role                 | ENUM            | USER, GUARDIAN, MINOR, ADMIN              |
| first_name           | VARCHAR(100)    | User's first name                         |
| last_name            | VARCHAR(100)    | User's last name                          |
| date_of_birth        | DATE            | User's date of birth                      |
| created_at           | TIMESTAMP       | Account creation timestamp                |
| updated_at           | TIMESTAMP       | Last update timestamp                     |
| last_login           | TIMESTAMP       | Last login timestamp                      |
| status               | ENUM            | ACTIVE, INACTIVE, SUSPENDED, BETA_TESTER  |
| two_factor_enabled   | BOOLEAN         | Whether 2FA is enabled                    |
| two_factor_secret    | VARCHAR(255)    | Secret for 2FA (encrypted)                |
| risk_profile         | ENUM            | LOW, MODERATE, AGGRESSIVE                 |
| education_progress   | JSONB           | Progress in educational modules           |
| preferences          | JSONB           | User preferences                          |
| beta_feedback        | TEXT            | Beta tester feedback                      |

### Portfolio

The Portfolio entity represents a collection of financial assets owned by a user.

**Table: `portfolios`**

| Column Name          | Type            | Description                               |
|----------------------|-----------------|-------------------------------------------|
| id                   | UUID            | Primary key                               |
| user_id              | UUID            | Foreign key to users table                |
| name                 | VARCHAR(100)    | Portfolio name                            |
| description          | TEXT            | Portfolio description                     |
| created_at           | TIMESTAMP       | Creation timestamp                        |
| updated_at           | TIMESTAMP       | Last update timestamp                     |
| cash_balance         | DECIMAL(15,2)   | Available cash balance                    |
| total_value          | DECIMAL(15,2)   | Total portfolio value including positions |
| risk_score           | INTEGER         | Risk assessment score (0-100)             |
| diversification_score| INTEGER         | Diversification score (0-100)             |
| type                 | ENUM            | STANDARD, EDUCATION, RETIREMENT           |
| guardian_approval    | BOOLEAN         | Whether guardian approval is required     |
| volatility_preference| ENUM            | LOW, NORMAL, HIGH, EXTREME                |
| performance_metrics  | JSONB           | Historical performance data               |

### Position

The Position entity represents an investment holding within a portfolio.

**Table: `positions`**

| Column Name          | Type            | Description                               |
|----------------------|-----------------|-------------------------------------------|
| id                   | UUID            | Primary key                               |
| portfolio_id         | UUID            | Foreign key to portfolios table           |
| symbol               | VARCHAR(20)     | Stock/asset symbol                        |
| quantity             | DECIMAL(15,6)   | Quantity owned                            |
| average_price        | DECIMAL(15,2)   | Average purchase price                    |
| current_price        | DECIMAL(15,2)   | Current market price                      |
| current_value        | DECIMAL(15,2)   | Current position value                    |
| created_at           | TIMESTAMP       | Position creation timestamp               |
| updated_at           | TIMESTAMP       | Last update timestamp                     |
| last_price_update    | TIMESTAMP       | Last price update timestamp               |
| gain_loss            | DECIMAL(15,2)   | Unrealized gain/loss                      |
| gain_loss_percent    | DECIMAL(10,2)   | Percentage gain/loss                      |
| asset_type           | ENUM            | STOCK, ETF, MUTUAL_FUND, CRYPTO, OTHER    |
| sector               | VARCHAR(100)    | Industry sector                           |

### Trade

The Trade entity represents a buy or sell transaction.

**Table: `trades`**

| Column Name          | Type            | Description                               |
|----------------------|-----------------|-------------------------------------------|
| id                   | UUID            | Primary key                               |
| portfolio_id         | UUID            | Foreign key to portfolios table           |
| symbol               | VARCHAR(20)     | Stock/asset symbol                        |
| order_type           | ENUM            | MARKET, LIMIT                             |
| side                 | ENUM            | BUY, SELL                                 |
| quantity             | DECIMAL(15,6)   | Quantity to trade                         |
| price                | DECIMAL(15,2)   | Execution price (or limit price)          |
| status               | ENUM            | PENDING, EXECUTED, CANCELLED, REJECTED    |
| created_at           | TIMESTAMP       | Order creation timestamp                  |
| executed_at          | TIMESTAMP       | Execution timestamp                       |
| total_amount         | DECIMAL(15,2)   | Total transaction amount                  |
| fees                 | DECIMAL(10,2)   | Transaction fees                          |
| notes                | TEXT            | Trade notes                               |
| circuit_breaker_state| ENUM            | OPEN, RESTRICTED, CAUTIOUS, CLOSED        |
| volatility_level     | ENUM            | LOW, NORMAL, HIGH, EXTREME                |
| guardian_approval    | ENUM            | PENDING, APPROVED, REJECTED, NOT_REQUIRED |
| confidence_score     | DECIMAL(5,2)    | ML model confidence (0-1)                 |
| position_sizing      | DECIMAL(5,2)    | Position sizing factor applied            |

### Relationship

The Relationship entity connects users in guardian-minor relationships.

**Table: `relationships`**

| Column Name          | Type            | Description                               |
|----------------------|-----------------|-------------------------------------------|
| id                   | UUID            | Primary key                               |
| guardian_id          | UUID            | Foreign key to guardian user              |
| minor_id             | UUID            | Foreign key to minor user                 |
| relationship_type    | ENUM            | PARENT, LEGAL_GUARDIAN, OTHER             |
| created_at           | TIMESTAMP       | Relationship creation timestamp           |
| updated_at           | TIMESTAMP       | Last update timestamp                     |
| status               | ENUM            | ACTIVE, INACTIVE, PENDING                 |
| approval_settings    | JSONB           | Guardian approval settings                |
| permissions          | JSONB           | Specific permissions granted              |

### Notification

The Notification entity stores messages and alerts sent to users.

**Table: `notifications`**

| Column Name          | Type            | Description                               |
|----------------------|-----------------|-------------------------------------------|
| id                   | UUID            | Primary key                               |
| user_id              | UUID            | Foreign key to users table                |
| related_entity_id    | UUID            | Optional related entity ID                |
| related_entity_type  | VARCHAR(50)     | Type of related entity                    |
| type                 | ENUM            | TRADE, APPROVAL, SYSTEM, EDUCATIONAL      |
| title                | VARCHAR(100)    | Notification title                        |
| message              | TEXT            | Notification message                      |
| created_at           | TIMESTAMP       | Creation timestamp                        |
| read_at              | TIMESTAMP       | When notification was read                |
| status               | ENUM            | UNREAD, READ, ARCHIVED                    |
| priority             | ENUM            | LOW, NORMAL, HIGH, URGENT                 |
| action_url           | VARCHAR(255)    | Optional URL for action                   |

## Trading Engine Data Model

### Volatility Regime

**Table: `volatility_regimes`**

| Column Name          | Type            | Description                               |
|----------------------|-----------------|-------------------------------------------|
| id                   | UUID            | Primary key                               |
| symbol               | VARCHAR(20)     | Stock/asset symbol                        |
| timestamp            | TIMESTAMP       | Measurement timestamp                     |
| volatility_value     | DECIMAL(10,4)   | Calculated volatility value               |
| volatility_level     | ENUM            | LOW, NORMAL, HIGH, EXTREME                |
| lookback_period      | INTEGER         | Lookback period in days                   |
| calculation_method   | VARCHAR(50)     | Method used for calculation               |
| circuit_breaker_state| ENUM            | OPEN, RESTRICTED, CAUTIOUS, CLOSED        |
| confidence_score     | DECIMAL(5,2)    | Confidence in regime classification       |
| stabilization_count  | INTEGER         | Consecutive same-regime detections        |

### Model Parameters

**Table: `model_parameters`**

| Column Name          | Type            | Description                               |
|----------------------|-----------------|-------------------------------------------|
| id                   | UUID            | Primary key                               |
| volatility_level     | ENUM            | LOW, NORMAL, HIGH, EXTREME                |
| parameter_type       | VARCHAR(50)     | Type of parameter                         |
| parameter_name       | VARCHAR(100)    | Name of parameter                         |
| parameter_value      | DECIMAL(15,6)   | Value of parameter                        |
| effective_from       | TIMESTAMP       | When parameter becomes effective          |
| effective_to         | TIMESTAMP       | When parameter expires                    |
| created_by           | VARCHAR(100)    | Creator of parameter setting              |
| created_at           | TIMESTAMP       | Creation timestamp                        |
| updated_at           | TIMESTAMP       | Last update timestamp                     |
| description          | TEXT            | Parameter description                     |

### Backtesting Results

**Table: `backtest_results`**

| Column Name          | Type            | Description                               |
|----------------------|-----------------|-------------------------------------------|
| id                   | UUID            | Primary key                               |
| model_version        | VARCHAR(50)     | Model version used                        |
| symbol               | VARCHAR(20)     | Stock/asset symbol                        |
| start_date           | DATE            | Backtest start date                       |
| end_date             | DATE            | Backtest end date                         |
| total_trades         | INTEGER         | Total number of trades                    |
| win_rate             | DECIMAL(5,2)    | Win rate percentage                       |
| profit_loss          | DECIMAL(15,2)   | Total profit/loss                         |
| sharpe_ratio         | DECIMAL(10,4)   | Sharpe ratio                              |
| drawdown_max         | DECIMAL(10,4)   | Maximum drawdown                          |
| volatility_breakdown | JSONB           | Performance by volatility regime          |
| parameters_used      | JSONB           | Parameters used in backtest               |
| created_at           | TIMESTAMP       | Test execution timestamp                  |
| notes                | TEXT            | Notes about the backtest                  |

## Beta-Specific Tables

### Beta Feedback

**Table: `beta_feedback`**

| Column Name          | Type            | Description                               |
|----------------------|-----------------|-------------------------------------------|
| id                   | UUID            | Primary key                               |
| user_id              | UUID            | Foreign key to users table                |
| feedback_type        | ENUM            | BUG, FEATURE_REQUEST, GENERAL             |
| category             | VARCHAR(100)    | Feedback category                         |
| title                | VARCHAR(255)    | Feedback title                            |
| description          | TEXT            | Detailed feedback                         |
| severity             | ENUM            | LOW, MEDIUM, HIGH, CRITICAL               |
| status               | ENUM            | NEW, REVIEWING, PRIORITIZED, IMPLEMENTED  |
| submitted_at         | TIMESTAMP       | Submission timestamp                      |
| updated_at           | TIMESTAMP       | Last update timestamp                     |
| related_component    | VARCHAR(100)    | Component feedback relates to             |
| environment_details  | JSONB           | User environment details                  |
| screenshots          | ARRAY           | Array of screenshot URLs                  |
| assigned_to          | UUID            | Team member assigned to address feedback  |

### Feature Flags

**Table: `feature_flags`**

| Column Name          | Type            | Description                               |
|----------------------|-----------------|-------------------------------------------|
| id                   | UUID            | Primary key                               |
| flag_name            | VARCHAR(100)    | Feature flag name                         |
| description          | TEXT            | Description of the feature                |
| enabled              | BOOLEAN         | Whether feature is enabled                |
| environment          | ENUM            | DEV, BETA, STAGING, PRODUCTION            |
| user_percentage      | INTEGER         | Percentage of users to enable for         |
| user_whitelist       | ARRAY           | Array of user IDs for targeted rollout    |
| created_at           | TIMESTAMP       | Creation timestamp                        |
| updated_at           | TIMESTAMP       | Last update timestamp                     |
| created_by           | VARCHAR(100)    | Creator of flag                           |
| expires_at           | TIMESTAMP       | When flag auto-expires                    |

## Database Indices

### Primary Indices

- `users`: `id`, `email`
- `portfolios`: `id`, `user_id`
- `positions`: `id`, `portfolio_id`, `symbol`
- `trades`: `id`, `portfolio_id`, `created_at`
- `relationships`: `id`, `guardian_id`, `minor_id`
- `notifications`: `id`, `user_id`, `created_at`
- `volatility_regimes`: `id`, `symbol`, `timestamp`
- `model_parameters`: `id`, `volatility_level`, `parameter_name`
- `backtest_results`: `id`, `model_version`, `symbol`
- `beta_feedback`: `id`, `user_id`, `submitted_at`
- `feature_flags`: `id`, `flag_name`, `environment`

### Performance Indices

- `users`: `(role, status)`, `last_login`
- `portfolios`: `total_value`
- `positions`: `(portfolio_id, asset_type)`, `current_value`
- `trades`: `(portfolio_id, status)`, `(symbol, side)`, `executed_at`
- `notifications`: `(user_id, status)`, `(user_id, type)`
- `volatility_regimes`: `(symbol, volatility_level)`, `circuit_breaker_state`
- `backtest_results`: `(symbol, model_version)`, `win_rate`
- `beta_feedback`: `(status, severity)`, `feedback_type`

## Migrations

Database migrations are managed through Alembic with the following principle migrations:

1. Initial schema creation
2. User role extensions
3. Portfolio analytics fields
4. Trading engine integration
5. Volatility regime tracking
6. Beta feedback mechanism
7. Feature flag system
8. Performance optimization indices

## Data Access Patterns

### Common Queries

1. **User Authentication**:
   ```sql
   SELECT id, password_hash, role, status FROM users WHERE email = ?
   ```

2. **Portfolio Overview**:
   ```sql
   SELECT p.*, COUNT(pos.id) AS position_count 
   FROM portfolios p
   LEFT JOIN positions pos ON p.id = pos.portfolio_id 
   WHERE p.user_id = ? 
   GROUP BY p.id
   ```

3. **Trade History**:
   ```sql
   SELECT * FROM trades 
   WHERE portfolio_id = ? 
   ORDER BY created_at DESC 
   LIMIT ? OFFSET ?
   ```

4. **Guardian Approval Queue**:
   ```sql
   SELECT t.*, p.name AS portfolio_name, u.first_name, u.last_name 
   FROM trades t
   JOIN portfolios p ON t.portfolio_id = p.id
   JOIN users u ON p.user_id = u.id
   JOIN relationships r ON u.id = r.minor_id
   WHERE r.guardian_id = ? AND t.guardian_approval = 'PENDING'
   ```

5. **Volatility Tracking**:
   ```sql
   SELECT * FROM volatility_regimes 
   WHERE symbol = ? 
   ORDER BY timestamp DESC 
   LIMIT 30
   ```

### Beta-Specific Queries

1. **Beta User Feedback Collection**:
   ```sql
   SELECT * FROM beta_feedback 
   WHERE user_id = ? 
   ORDER BY submitted_at DESC
   ```

2. **Feature Flag Evaluation**:
   ```sql
   SELECT * FROM feature_flags 
   WHERE environment = 'BETA' AND enabled = TRUE
   ```

## Data Consistency Rules

1. **User Accounts**:
   - Email addresses must be unique
   - Minors must have at least one guardian relationship

2. **Portfolios**:
   - Cash balance cannot be negative
   - Total value must equal sum of positions + cash

3. **Trades**:
   - Sell trades require sufficient position quantity
   - Buy trades require sufficient cash balance
   - Trades for minors require guardian approval if enabled

4. **Volatility Regimes**:
   - Stabilization count must be ≥ 3 for regime changes
   - Circuit breaker state changes follow graduated progression

## Data Security

1. **Encryption**:
   - Personal identifiable information (PII) is encrypted at rest
   - Authentication credentials use bcrypt hashing
   - Two-factor secrets are encrypted with envelope encryption

2. **Access Controls**:
   - Row-level security policies restrict data access
   - Role-based access control for all entities
   - Audit logging for sensitive data access

3. **Beta Safeguards**:
   - Beta user data is isolated from production
   - Daily snapshots for beta environment recovery
   - Sanitized seed data for testing

## Performance Considerations

1. **Partitioning**:
   - Time-based partitioning for trades and volatility data
   - User-based sharding for notification data

2. **Caching**:
   - Frequently accessed portfolio data is cached
   - Market data uses short TTL caching
   - Authentication tokens cached for fast validation

3. **Query Optimization**:
   - Covering indices for common query patterns
   - Materialized views for complex analytics queries
   - Regular VACUUM and index maintenance