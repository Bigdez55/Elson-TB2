# Elson-TB2 Architecture

**Document Version**: 2.0 (Post-Optimization)
**Last Updated**: 2025-12-02
**Status**: Proposed

---

## 🏛️ System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          USERS                                   │
│                     (Web Browser)                                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React SPA)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Dashboard   │  │  Portfolio   │  │   Trading    │          │
│  │    Pages     │  │    Pages     │  │    Pages     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Redux Store (State Management)                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         API Client (Axios)                               │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ REST API (JSON)
                         │ /api/v1/*
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                 BACKEND (FastAPI Server)                         │
│                                                                  │
│  ┌────────────────── API Layer ─────────────────────────────┐  │
│  │ /auth  /portfolio  /trading  /market  /ai  /advanced     │  │
│  └───────────────────────┬───────────────────────────────────┘  │
│                          │                                       │
│  ┌────────────────── Module Layer ──────────────────────────┐  │
│  │                                                           │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │  │
│  │  │  Auth   │  │Portfolio│  │ Trading │  │ Market  │    │  │
│  │  │ Module  │  │ Module  │  │ Module  │  │  Data   │    │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │  │
│  │                                                           │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │  │
│  │  │  AI/ML  │  │Strategy │  │  Risk   │  │Analytics│    │  │
│  │  │ Module  │  │ Module  │  │ Module  │  │ Module  │    │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │  │
│  │                                                           │  │
│  └───────────────────────┬───────────────────────────────────┘  │
│                          │                                       │
│  ┌──────────────── Shared Kernel ──────────────────────────┐  │
│  │  Database  │  Security  │  Cache  │  Exceptions          │  │
│  └───────────────────────┬───────────────────────────────────┘  │
│                          │                                       │
└──────────────────────────┼───────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  PostgreSQL  │  │    Redis     │  │  SQLite      │
│ (Production) │  │   (Cache)    │  │    (Dev)     │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## 📦 Module Architecture (Proposed)

### Backend Module Structure

```
backend/app/
├── main.py                          # FastAPI application
│
├── api/api_v1/                      # HTTP layer
│   ├── api.py                       # Router aggregator
│   └── endpoints/                   # API endpoints
│       ├── auth.py                  # → auth module
│       ├── portfolio.py             # → portfolio module
│       ├── trading.py               # → trading module
│       ├── market_data.py           # → market_data module
│       ├── ai_trading.py            # → ai_ml module
│       └── advanced_trading.py      # → strategy module
│
├── modules/                         # 🆕 Domain modules
│   ├── auth/                        # Authentication domain
│   │   ├── service.py               # Business logic
│   │   ├── repository.py            # Data access
│   │   ├── models.py                # ORM models
│   │   └── schemas.py               # DTOs
│   │
│   ├── portfolio/                   # Portfolio domain
│   │   ├── service.py
│   │   ├── optimizer.py             # MPT optimization
│   │   ├── repository.py
│   │   ├── models.py
│   │   └── schemas.py
│   │
│   ├── trading/                     # Trading domain
│   │   ├── service.py
│   │   ├── broker_adapter.py        # Alpaca integration
│   │   ├── repository.py
│   │   ├── models.py
│   │   └── schemas.py
│   │
│   ├── market_data/                 # Market data domain
│   │   ├── service.py
│   │   ├── providers/               # Data providers
│   │   │   ├── alpha_vantage.py
│   │   │   ├── polygon.py
│   │   │   └── yfinance.py
│   │   └── processor.py             # Data cleaning
│   │
│   ├── ai_ml/                       # AI/ML domain
│   │   ├── service.py
│   │   ├── models/                  # ML models
│   │   │   ├── xgboost_predictor.py
│   │   │   ├── neural_network.py
│   │   │   └── ensemble.py
│   │   └── training.py
│   │
│   ├── strategy/                    # Trading strategy domain
│   │   ├── service.py
│   │   ├── engine.py
│   │   └── backtest.py
│   │
│   ├── risk/                        # Risk management domain
│   │   ├── service.py
│   │   ├── circuit_breaker.py
│   │   └── position_sizing.py
│   │
│   └── analytics/                   # Analytics domain
│       ├── service.py
│       ├── performance.py
│       └── reporting.py
│
├── shared/                          # 🆕 Shared kernel
│   ├── database.py                  # DB session management
│   ├── security.py                  # JWT, hashing
│   ├── cache.py                     # Redis client
│   ├── exceptions.py                # Custom exceptions
│   └── utils.py                     # Common utilities
│
└── core/                            # Core configuration
    └── config.py                    # Settings
```

---

### Frontend Workspace Structure

```
frontend/
├── package.json                     # Workspace root
├── pnpm-workspace.yaml              # 🆕 Workspace config
├── turbo.json                       # 🆕 Build orchestration
│
├── apps/                            # 🆕 Applications
│   └── web/                         # Main web app
│       ├── package.json
│       ├── src/
│       │   ├── App.tsx
│       │   ├── pages/
│       │   │   ├── DashboardPage.tsx
│       │   │   ├── PortfolioPage.tsx
│       │   │   └── TradingPage.tsx
│       │   └── routes/
│       │       └── index.tsx
│       └── Dockerfile
│
└── packages/                        # 🆕 Shared packages
    ├── api-client/                  # API service layer
    │   ├── package.json
    │   ├── src/
    │   │   ├── auth.ts
    │   │   ├── portfolio.ts
    │   │   └── trading.ts
    │   └── tsconfig.json
    │
    ├── state/                       # Redux store
    │   ├── package.json
    │   ├── src/
    │   │   ├── authSlice.ts
    │   │   ├── portfolioSlice.ts
    │   │   └── store.ts
    │   └── tsconfig.json
    │
    ├── types/                       # TypeScript types
    │   ├── package.json
    │   ├── src/
    │   │   ├── auth.ts
    │   │   ├── portfolio.ts
    │   │   └── trading.ts
    │   └── tsconfig.json
    │
    └── config/                      # Shared configs
        ├── eslint-config/
        ├── tsconfig/
        └── tailwind-config/
```

---

### Packages (Shared Libraries)

```
packages/
├── trading-core/                    # Core trading algorithms
│   ├── setup.py
│   ├── src/trading_core/
│   │   ├── strategies/
│   │   │   ├── base.py
│   │   │   ├── moving_average.py
│   │   │   └── combined.py
│   │   ├── engine/
│   │   │   ├── execution.py
│   │   │   └── backtest.py
│   │   └── types.py
│   └── tests/
│
├── ml-models/                       # ML/AI components
│   ├── setup.py
│   ├── src/ml_models/
│   │   ├── models/
│   │   │   ├── xgboost_model.py
│   │   │   ├── ensemble.py
│   │   │   └── volatility_regime.py
│   │   ├── training/
│   │   │   ├── trainer.py
│   │   │   └── evaluator.py
│   │   └── types.py
│   └── tests/
│
├── risk-management/                 # Risk & compliance
│   ├── setup.py
│   ├── src/risk/
│   │   ├── calculator.py
│   │   ├── compliance.py
│   │   ├── circuit_breaker.py
│   │   └── position_sizing.py
│   └── tests/
│
├── market-data/                     # Data providers
│   ├── setup.py
│   ├── src/market_data/
│   │   ├── providers/
│   │   │   ├── alpha_vantage.py
│   │   │   ├── polygon.py
│   │   │   └── yfinance.py
│   │   ├── sentiment/
│   │   │   └── analyzer.py
│   │   └── types.py
│   └── tests/
│
├── tax-reporting/                   # 🆕 Tax calculations (future)
│   ├── setup.py
│   ├── src/tax/
│   │   ├── calculator.py
│   │   ├── wash_sales.py
│   │   └── form_1099.py
│   └── tests/
│
├── planning/                        # 🆕 Financial planning (future)
│   ├── setup.py
│   ├── src/planning/
│   │   ├── goal_tracker.py
│   │   └── retirement.py
│   └── tests/
│
└── ui-components/                   # 🆕 React component library
    ├── package.json
    ├── src/
    │   ├── components/
    │   │   ├── portfolio/
    │   │   ├── trading/
    │   │   ├── charts/
    │   │   └── ai/
    │   ├── hooks/
    │   └── utils/
    ├── tailwind.config.js
    └── tests/
```

---

## 🔗 Dependency Graph

### Module Dependencies (Backend)

```
┌─────────────────────────────────────────────────────────────────┐
│                     API Layer (HTTP)                             │
│  /auth  /portfolio  /trading  /market  /ai  /advanced           │
└─────────┬───────────────────────────────────────────────────────┘
          │
          │ (calls)
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Domain Modules (Business Logic)                │
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │   Auth   │    │Portfolio │    │ Trading  │    │  Market  │ │
│  │          │◄───│          │◄───│          │◄───│   Data   │ │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│                        │               │                        │
│                        ▼               ▼                        │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                 │
│  │  AI/ML   │◄───│ Strategy │───►│   Risk   │                 │
│  │          │    │          │    │          │                 │
│  └──────────┘    └──────────┘    └──────────┘                 │
│                        │                                        │
│                        ▼                                        │
│                  ┌──────────┐                                  │
│                  │Analytics │                                  │
│                  │          │                                  │
│                  └──────────┘                                  │
└─────────┬───────────────────────────────────────────────────────┘
          │
          │ (uses)
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Shared Kernel (Infrastructure)                  │
│  Database  │  Security  │  Cache  │  Exceptions  │  Utils       │
└─────────────────────────────────────────────────────────────────┘

Legend:
  ──► : Direct dependency
  ◄── : Uses/Imports
```

### Dependency Rules

1. **API Layer** can depend on **Domain Modules**
2. **Domain Modules** can depend on **Shared Kernel**
3. **Domain Modules** can depend on other **Domain Modules** (limited)
4. **Shared Kernel** cannot depend on **Domain Modules** (circular dep prevention)
5. **No circular dependencies** between modules

---

### Package Dependencies (Cross-Language)

```
Frontend (TypeScript)
    │
    ├─► ui-components (React)
    │
    └─► api-client ──► Backend API ──┐
                                     │
                            ┌────────▼────────┐
                            │   Backend       │
                            │   (FastAPI)     │
                            └────────┬────────┘
                                     │
        ┌────────────────────────────┼────────────────┐
        │                            │                │
        ▼                            ▼                ▼
  trading-core              ml-models          risk-management
        │                            │                │
        └────────────────────────────┴────────────────┘
                                     │
                                     ▼
                              market-data
                                     │
                                     ▼
                        External APIs (Alpaca, Alpha Vantage)
```

---

## 🚀 Data Flow Examples

### Example 1: User Login

```
1. User enters credentials in frontend
   └─► frontend/apps/web/LoginPage.tsx

2. Frontend calls auth API
   └─► frontend/packages/api-client/src/auth.ts
       POST /api/v1/auth/login

3. Backend receives request
   └─► backend/app/api/api_v1/endpoints/auth.py

4. Auth endpoint calls auth service
   └─► backend/app/modules/auth/service.py
       AuthService.authenticate()

5. Service uses repository to query database
   └─► backend/app/modules/auth/repository.py
       UserRepository.get_by_email()

6. Service verifies password
   └─► backend/app/shared/security.py
       verify_password()

7. Service creates JWT token
   └─► backend/app/shared/security.py
       create_access_token()

8. Token returned to frontend
   └─► frontend/packages/state/src/authSlice.ts
       Redux stores token

9. Future requests include token in Authorization header
```

---

### Example 2: Generate Trading Signal

```
1. User clicks "Generate Signal" in frontend
   └─► frontend/apps/web/TradingPage.tsx

2. Frontend calls advanced trading API
   └─► frontend/packages/api-client/src/advancedTrading.ts
       POST /api/v1/advanced/signals

3. Backend receives request
   └─► backend/app/api/api_v1/endpoints/advanced_trading.py

4. Endpoint calls strategy service
   └─► backend/app/modules/strategy/service.py
       StrategyService.generate_signals()

5. Strategy service gets market data
   └─► backend/app/modules/market_data/service.py
       MarketDataService.get_historical_data()

6. Market data service calls provider
   └─► backend/app/modules/market_data/providers/alpha_vantage.py
       AlphaVantageProvider.get_daily_data()

7. Strategy service imports trading algorithm
   └─► packages/trading-core/src/strategies/moving_average.py
       MovingAverageStrategy.generate_signals()

8. Strategy service calls AI model
   └─► backend/app/modules/ai_ml/service.py
       AIService.predict()

9. AI service imports ML model
   └─► packages/ml-models/src/models/xgboost_model.py
       XGBoostPredictor.predict()

10. Strategy service checks risk limits
    └─► backend/app/modules/risk/service.py
        RiskService.validate_signal()

11. Signal returned to frontend
    └─► frontend/packages/state/src/tradingSlice.ts
        Redux updates signals

12. Frontend displays signal
    └─► frontend/apps/web/TradingPanel.tsx
```

---

## 🛠️ Technology Stack by Layer

### Frontend

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Framework** | React 18 | UI library |
| **Language** | TypeScript 4.9 | Type safety |
| **State** | Redux Toolkit | Global state |
| **Routing** | React Router 6 | Client-side routing |
| **Styling** | Tailwind CSS | Utility-first CSS |
| **Charts** | Recharts | Data visualization |
| **API Client** | Axios | HTTP requests |
| **Build** | Vite (future) / CRA | Build tool |
| **Package Manager** | pnpm | Workspace management |
| **Build Orchestrator** | Turborepo | Caching & parallelization |

---

### Backend

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Framework** | FastAPI | REST API |
| **Language** | Python 3.12 | Backend language |
| **ORM** | SQLAlchemy | Database access |
| **Database** | PostgreSQL / SQLite | Data persistence |
| **Cache** | Redis | Caching layer |
| **Auth** | JWT + bcrypt | Authentication |
| **Validation** | Pydantic | Request/response schemas |
| **Logging** | Structlog | Structured logging |
| **Testing** | pytest | Unit/integration tests |
| **Package Manager** | pip / Poetry (future) | Dependency management |

---

### Shared Packages

| Package | Language | Technology |
|---------|----------|------------|
| **trading-core** | Python | NumPy, Pandas, TA-Lib |
| **ml-models** | Python | XGBoost, TensorFlow, PyTorch, Qiskit |
| **risk-management** | Python | NumPy, Pandas |
| **market-data** | Python | Requests, WebSockets, TextBlob, VADER |
| **ui-components** | TypeScript | React, Tailwind CSS, Recharts |

---

### External APIs

| Service | Purpose | Protocol |
|---------|---------|----------|
| **Alpha Vantage** | Market data | REST API |
| **Polygon.io** | Real-time quotes | REST API / WebSocket |
| **Alpaca Markets** | Paper trading | REST API / WebSocket |
| **yfinance** | Backup market data | Python library |

---

## 🔐 Security Architecture

### Authentication Flow

```
┌─────────┐              ┌─────────┐              ┌─────────┐
│ Browser │              │ Backend │              │Database │
└────┬────┘              └────┬────┘              └────┬────┘
     │                        │                        │
     │ POST /auth/login       │                        │
     │ {email, password}      │                        │
     ├───────────────────────►│                        │
     │                        │                        │
     │                        │ SELECT * FROM users    │
     │                        │ WHERE email = ?        │
     │                        ├───────────────────────►│
     │                        │                        │
     │                        │◄───────────────────────┤
     │                        │ User record            │
     │                        │                        │
     │                        │ verify_password()      │
     │                        │ (bcrypt)               │
     │                        │                        │
     │                        │ create_access_token()  │
     │                        │ (JWT)                  │
     │                        │                        │
     │◄───────────────────────┤                        │
     │ {access_token: "..."}  │                        │
     │                        │                        │
     │ GET /portfolio         │                        │
     │ Authorization: Bearer  │                        │
     │ eyJ0eXAiOiJKV1QiLi...  │                        │
     ├───────────────────────►│                        │
     │                        │                        │
     │                        │ verify_token()         │
     │                        │ (JWT decode)           │
     │                        │                        │
     │                        │ get_user(user_id)      │
     │                        ├───────────────────────►│
     │                        │◄───────────────────────┤
     │                        │                        │
     │◄───────────────────────┤                        │
     │ Portfolio data         │                        │
     │                        │                        │
```

---

## 📊 Deployment Architecture

### Development (Local)

```
┌──────────────────────────────────────────────────────────┐
│                     Developer Machine                     │
│                                                           │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐         │
│  │  Frontend  │  │  Backend   │  │   Redis    │         │
│  │            │  │            │  │            │         │
│  │ npm start  │  │ uvicorn    │  │ redis-srv  │         │
│  │ :3000      │  │ :8080      │  │ :6379      │         │
│  └────────────┘  └────────────┘  └────────────┘         │
│                                                           │
│  SQLite (./elson_trading.db)                             │
└──────────────────────────────────────────────────────────┘
```

---

### Production (Google Cloud Run)

```
                          ┌─────────────────┐
                          │ Cloud Load      │
                          │ Balancer        │
                          │ (HTTPS)         │
                          └────────┬────────┘
                                   │
                ┌──────────────────┼──────────────────┐
                │                  │                  │
                ▼                  ▼                  ▼
        ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
        │ Cloud Run    │  │ Cloud Run    │  │ Cloud Run    │
        │ Instance 1   │  │ Instance 2   │  │ Instance 3   │
        │ (Backend)    │  │ (Backend)    │  │ (Backend)    │
        └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
               │                  │                  │
               └──────────────────┼──────────────────┘
                                  │
                   ┌──────────────┼──────────────┐
                   │              │              │
                   ▼              ▼              ▼
         ┌──────────────┐  ┌──────────┐  ┌──────────┐
         │ Cloud SQL    │  │ Memstore │  │ Secret   │
         │ (PostgreSQL) │  │ (Redis)  │  │ Manager  │
         └──────────────┘  └──────────┘  └──────────┘
```

---

## 📈 Performance Optimization

### Caching Strategy

```
Request → Check Redis Cache
            │
            ├─► Cache Hit
            │   └─► Return cached data
            │
            └─► Cache Miss
                └─► Query database/API
                    └─► Store in Redis (TTL: 5 min)
                        └─► Return data
```

### Build Optimization (Turborepo)

```
pnpm build

Turbo checks:
1. Has source changed? (git hash)
   └─► No → Return cached output (instant!)
   └─► Yes → Continue

2. Have dependencies changed?
   └─► No → Use dependency cache
   └─► Yes → Rebuild dependencies first

3. Build module
   └─► Store output in cache (.turbo/)
   └─► Return success
```

---

## 📝 Key Design Principles

1. **Modularity**: Each module owns its domain logic, models, and schemas
2. **Separation of Concerns**: HTTP layer, business logic, and data access are separated
3. **Dependency Inversion**: Modules depend on abstractions (interfaces), not implementations
4. **Single Responsibility**: Each module has one clear responsibility
5. **Open/Closed**: Modules are open for extension, closed for modification
6. **Interface Segregation**: Modules expose only what's needed in public API
7. **Don't Repeat Yourself**: Shared logic lives in packages or shared kernel

---

## 🚀 Future Enhancements

### Phase 1 (Next 3 Months)
- [ ] Complete backend module refactor
- [ ] Set up pnpm + Turborepo
- [ ] Implement CI change detection
- [ ] Extract ui-components package

### Phase 2 (Next 6 Months)
- [ ] Add tax-reporting module
- [ ] Add financial planning module
- [ ] Implement remote caching (Vercel)
- [ ] Set up dependency graph monitoring

### Phase 3 (Next 12 Months)
- [ ] Microservices extraction (if needed)
- [ ] Event-driven architecture (Kafka/RabbitMQ)
- [ ] Real-time WebSocket for market data
- [ ] Mobile app (React Native)

---

**Document Maintainer**: Elson Trading Platform Team
**Review Cycle**: Quarterly
**Next Review**: 2025-03-02
