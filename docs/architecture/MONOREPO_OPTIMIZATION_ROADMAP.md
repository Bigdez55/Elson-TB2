# Monorepo Optimization Roadmap

**Goal**: Refine module boundaries and add modern monorepo tooling while maintaining the existing 3-module structure.

**Status**: Planning Phase
**Estimated Timeline**: 4-6 weeks
**Risk Level**: Low (incremental improvements, no architectural rewrite)

---

## 📋 Executive Summary

The Elson-TB2 repository is already a **well-structured multi-module monorepo**. The next optimization focuses on:

1. **Refining sub-module boundaries** within existing modules
2. **Adding JavaScript workspace tooling** (pnpm + Turbo recommended)
3. **Implementing CI change-detection** for faster builds
4. **Establishing clear module contracts** with explicit APIs

**Key Principle**: Keep the monorepo, enhance the modularity.

---

## 🎯 Current State Analysis

### ✅ What's Working Well
- Clear 3-module separation (backend, frontend, elson-trading-package)
- Docker-based deployment
- Shared configuration files
- Single git repository for versioning

### ⚠️ Areas for Improvement
- **Backend**: Services are flat; no clear domain boundaries (10 services in one directory)
- **elson-trading-package**: Multiple concerns mixed (UI + ML + trading + risk)
- **JavaScript**: No workspace tooling; frontend and package/ui are separate builds
- **CI/CD**: Builds everything on every commit (no change detection)
- **Dependencies**: Unclear which modules depend on what

---

## 🏗️ Phase 1: Refine Module Boundaries (Week 1-2)

### A. Backend Sub-Module Structure

**Current Problem**: All services in flat `backend/app/services/` directory

**Proposed Structure**:
```
backend/
├── app/
│   ├── main.py                      # FastAPI app
│   ├── api/api_v1/                  # HTTP layer (unchanged)
│   │
│   ├── modules/                     # 🆕 Domain-driven modules
│   │   ├── auth/                    # Authentication domain
│   │   │   ├── __init__.py
│   │   │   ├── service.py           # Auth business logic
│   │   │   ├── models.py            # User ORM model
│   │   │   ├── schemas.py           # Auth DTOs
│   │   │   └── repository.py        # DB access layer
│   │   │
│   │   ├── portfolio/               # Portfolio management domain
│   │   │   ├── __init__.py
│   │   │   ├── service.py           # Portfolio service
│   │   │   ├── optimizer.py         # MPT optimization
│   │   │   ├── models.py            # Portfolio ORM
│   │   │   └── schemas.py           # Portfolio DTOs
│   │   │
│   │   ├── trading/                 # Trading execution domain
│   │   │   ├── __init__.py
│   │   │   ├── service.py           # Trading service
│   │   │   ├── broker_adapter.py    # Alpaca integration
│   │   │   ├── models.py            # Trade ORM
│   │   │   └── schemas.py           # Trading DTOs
│   │   │
│   │   ├── market_data/             # Market data domain
│   │   │   ├── __init__.py
│   │   │   ├── service.py           # Data aggregation
│   │   │   ├── providers/           # Provider adapters
│   │   │   │   ├── alpha_vantage.py
│   │   │   │   ├── polygon.py
│   │   │   │   └── yfinance.py
│   │   │   └── processor.py         # Data cleaning
│   │   │
│   │   ├── ai_ml/                   # AI/ML domain
│   │   │   ├── __init__.py
│   │   │   ├── service.py           # ML orchestration
│   │   │   ├── models/              # ML model wrappers
│   │   │   │   ├── xgboost_predictor.py
│   │   │   │   ├── neural_network.py
│   │   │   │   └── ensemble.py
│   │   │   └── training.py          # Model training
│   │   │
│   │   ├── strategy/                # Trading strategy domain
│   │   │   ├── __init__.py
│   │   │   ├── service.py           # Strategy execution
│   │   │   ├── engine.py            # Strategy engine
│   │   │   └── backtest.py          # Backtesting
│   │   │
│   │   ├── risk/                    # Risk management domain
│   │   │   ├── __init__.py
│   │   │   ├── service.py           # Risk calculations
│   │   │   ├── circuit_breaker.py   # Trading limits
│   │   │   └── position_sizing.py   # Position management
│   │   │
│   │   └── analytics/               # Reporting & analytics domain
│   │       ├── __init__.py
│   │       ├── service.py           # Analytics service
│   │       ├── performance.py       # Performance metrics
│   │       └── reporting.py         # Report generation
│   │
│   ├── shared/                      # 🆕 Shared kernel
│   │   ├── database.py              # DB session management
│   │   ├── security.py              # JWT, hashing
│   │   ├── cache.py                 # Redis client
│   │   ├── exceptions.py            # Custom exceptions
│   │   └── utils.py                 # Common utilities
│   │
│   └── core/                        # Core configuration (unchanged)
│       └── config.py
```

**Benefits**:
- Clear domain boundaries
- Each module owns its models, schemas, service, repository
- Easy to test modules in isolation
- Clear dependency graph

---

### B. elson-trading-package Sub-Module Structure

**Current Problem**: Multiple unrelated concerns in one package

**Proposed Structure**:
```
packages/                            # 🆕 Rename for clarity
├── trading-core/                    # Core trading algorithms
│   ├── package.json
│   ├── setup.py
│   ├── strategies/
│   │   ├── moving_average.py
│   │   └── combined.py
│   ├── engine/
│   │   ├── execution.py
│   │   └── backtest.py
│   └── README.md
│
├── ml-models/                       # ML/AI components
│   ├── package.json
│   ├── setup.py
│   ├── models/
│   │   ├── xgboost_model.py
│   │   ├── ensemble.py
│   │   └── volatility_regime.py
│   ├── training/
│   └── README.md
│
├── risk-management/                 # Risk & compliance
│   ├── setup.py
│   ├── risk_calculator.py
│   ├── compliance_checker.py
│   ├── circuit_breaker.py
│   └── README.md
│
├── market-data/                     # Data providers & sentiment
│   ├── setup.py
│   ├── providers/
│   │   ├── alpha_vantage.py
│   │   └── polygon.py
│   ├── sentiment/
│   │   └── sentiment_analyzer.py
│   └── README.md
│
├── tax-reporting/                   # 🆕 Tax & compliance (future)
│   ├── setup.py
│   ├── tax_calculator.py
│   ├── wash_sales.py
│   └── 1099_generator.py
│
├── planning/                        # 🆕 Financial planning (future)
│   ├── setup.py
│   ├── goal_tracker.py
│   └── retirement_planner.py
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
    └── README.md
```

**Module Contracts**:
- Each package has its own `setup.py` (Python) or `package.json` (JavaScript)
- Clear README with API documentation
- Explicit dependencies in `requirements.txt` or `package.json`
- Can be versioned and published independently (future)

---

### C. Frontend Workspace Structure

**Current Problem**: Frontend is monolithic; no code splitting by domain

**Proposed Structure**:
```
frontend/
├── package.json                     # Workspace root
├── apps/                            # 🆕 Applications
│   └── web/                         # Main web app
│       ├── package.json
│       ├── src/
│       │   ├── App.tsx
│       │   ├── pages/
│       │   └── routes/
│       ├── Dockerfile
│       └── nginx.conf
│
└── packages/                        # 🆕 Shared frontend packages
    ├── api-client/                  # API service layer
    │   ├── package.json
    │   ├── src/
    │   │   ├── auth.ts
    │   │   ├── portfolio.ts
    │   │   └── trading.ts
    │   └── README.md
    │
    ├── state/                       # Redux store
    │   ├── package.json
    │   ├── src/
    │   │   ├── authSlice.ts
    │   │   ├── portfolioSlice.ts
    │   │   └── store.ts
    │   └── README.md
    │
    ├── types/                       # TypeScript types
    │   ├── package.json
    │   ├── src/
    │   │   ├── auth.ts
    │   │   ├── portfolio.ts
    │   │   └── trading.ts
    │   └── README.md
    │
    └── config/                      # Shared configs
        ├── eslint-config/
        ├── tsconfig/
        └── tailwind-config/
```

---

## 🔧 Phase 2: Add Monorepo Tooling (Week 2-3)

### JavaScript Workspace Manager: **pnpm + Turborepo**

#### Why This Combo?

| Tool | Purpose | Benefits |
|------|---------|----------|
| **pnpm** | Package manager | 3x faster, disk-efficient, strict by default |
| **Turborepo** | Build orchestrator | Caching, parallelization, change detection |

**Alternative**: Nx (more features but heavier, better for large teams)

#### Implementation Plan

**1. Install pnpm**
```bash
npm install -g pnpm@8
```

**2. Create workspace root**
```yaml
# pnpm-workspace.yaml
packages:
  - 'frontend/apps/*'
  - 'frontend/packages/*'
  - 'packages/ui-components'
```

**3. Migrate package.json files**
```json
// frontend/package.json (root)
{
  "name": "elson-trading-monorepo",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "turbo run dev",
    "build": "turbo run build",
    "test": "turbo run test",
    "lint": "turbo run lint"
  },
  "devDependencies": {
    "turbo": "^1.11.0"
  }
}
```

**4. Configure Turborepo**
```json
// turbo.json
{
  "$schema": "https://turbo.build/schema.json",
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", "build/**"]
    },
    "test": {
      "dependsOn": ["build"],
      "outputs": []
    },
    "lint": {
      "outputs": []
    },
    "dev": {
      "cache": false,
      "persistent": true
    }
  }
}
```

**Benefits**:
- ✅ Run `pnpm build` and Turbo builds only changed packages
- ✅ Caches build outputs (2nd builds are instant)
- ✅ Parallel execution across CPU cores
- ✅ Visualize dependency graph: `pnpm turbo run build --graph`

---

### Python Monorepo Tooling

#### Package Manager: **Poetry** (Optional Enhancement)

**Current**: Using `requirements.txt`
**Upgrade**: Poetry for better dependency resolution

```toml
# backend/pyproject.toml
[tool.poetry]
name = "elson-trading-backend"
version = "1.0.0"

[tool.poetry.dependencies]
python = "^3.12"
fastapi = "^0.104.1"
sqlalchemy = "^2.0.23"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"
```

**Benefits**:
- Lock file for reproducible builds
- Better dependency resolution
- Virtual environment management

#### Task Runner: **Taskfile** or **Make**

```yaml
# Taskfile.yml
version: '3'

tasks:
  test:backend:
    dir: backend
    cmds:
      - pytest app/tests

  test:packages:
    dir: packages
    cmds:
      - pytest trading-core/tests
      - pytest ml-models/tests

  test:all:
    deps: [test:backend, test:packages]
```

---

## 🚀 Phase 3: CI Change Detection (Week 3-4)

### GitHub Actions Optimization

**Current Problem**: Builds everything on every commit

**Solution**: Use `paths` filters + Turborepo remote caching

#### Modified CI Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  # Detect changed files
  changes:
    runs-on: ubuntu-latest
    outputs:
      backend: ${{ steps.filter.outputs.backend }}
      frontend: ${{ steps.filter.outputs.frontend }}
      packages: ${{ steps.filter.outputs.packages }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v2
        id: filter
        with:
          filters: |
            backend:
              - 'backend/**'
              - 'packages/trading-core/**'
              - 'packages/ml-models/**'
            frontend:
              - 'frontend/**'
              - 'packages/ui-components/**'
            packages:
              - 'packages/**'

  # Backend tests (only if backend changed)
  test-backend:
    needs: changes
    if: needs.changes.outputs.backend == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          pytest app/tests --cov

  # Frontend tests (only if frontend changed)
  test-frontend:
    needs: changes
    if: needs.changes.outputs.frontend == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
        with:
          version: 8
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'pnpm'
      - name: Install dependencies
        run: pnpm install --frozen-lockfile
      - name: Build
        run: pnpm turbo run build --filter=web
      - name: Test
        run: pnpm turbo run test --filter=web

  # Security scanning (always run)
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Trivy scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
```

**Performance Gains**:
- Frontend-only changes: Skip backend tests (save ~3 min)
- Backend-only changes: Skip frontend build (save ~2 min)
- Package changes: Only rebuild affected modules

---

### Turborepo Remote Caching (Advanced)

```json
// turbo.json
{
  "remoteCache": {
    "enabled": true
  }
}
```

**Setup**:
1. Sign up for Vercel (free tier)
2. `pnpm turbo login`
3. `pnpm turbo link`

**Benefit**: Share build cache across CI runs and developers

---

## 📐 Phase 4: Module Contracts & Documentation (Week 4-5)

### Define Explicit Module APIs

#### Example: Trading Core Package

```python
# packages/trading-core/src/trading_core/__init__.py
"""
Trading Core Package

Public API for trading strategies and execution.
"""

from .strategies import (
    BaseStrategy,
    MovingAverageStrategy,
    CombinedStrategy,
)
from .engine import (
    TradingEngine,
    BacktestEngine,
)
from .types import (
    Signal,
    Order,
    Position,
)

__all__ = [
    'BaseStrategy',
    'MovingAverageStrategy',
    'CombinedStrategy',
    'TradingEngine',
    'BacktestEngine',
    'Signal',
    'Order',
    'Position',
]

__version__ = '1.0.0'
```

**Benefits**:
- Clear public API (what can be imported)
- Internal implementation can change without breaking consumers
- Easy to version and deprecate APIs

---

### Dependency Graph Documentation

**Tool**: `pydeps` (Python), `madge` (JavaScript)

```bash
# Generate dependency graph
pydeps backend/app --max-bacon=2 -o docs/backend-deps.svg

# Find circular dependencies
madge --circular frontend/src
```

**Create ARCHITECTURE.md**:
```markdown
# Module Dependency Graph

## Backend Modules
```
auth → database
portfolio → database, market_data
trading → portfolio, broker_adapter
ai_ml → market_data, strategy
```

## Package Dependencies
```
trading-core → (no dependencies)
ml-models → trading-core
risk-management → trading-core
market-data → (external APIs only)
ui-components → (React only)
```

## Rules
1. No circular dependencies
2. Shared modules cannot depend on domain modules
3. Frontend packages cannot import backend code
```

---

## 🧪 Phase 5: Testing & Validation (Week 5-6)

### Module Isolation Tests

```python
# backend/tests/modules/test_portfolio_module.py
def test_portfolio_module_imports():
    """Ensure portfolio module has no forbidden dependencies."""
    import sys
    import importlib

    # Should succeed
    from app.modules.portfolio import service

    # Should NOT import trading or ai_ml
    assert 'app.modules.trading' not in sys.modules
    assert 'app.modules.ai_ml' not in sys.modules
```

### Contract Testing

```typescript
// packages/api-client/tests/contracts.test.ts
describe('Portfolio API Contract', () => {
  it('should match backend response schema', async () => {
    const response = await portfolioAPI.getPortfolio(1);

    expect(response).toMatchSchema({
      id: expect.any(Number),
      name: expect.any(String),
      total_value: expect.any(Number),
      holdings: expect.arrayContaining([
        expect.objectContaining({
          symbol: expect.any(String),
          quantity: expect.any(Number),
          current_price: expect.any(Number),
        }),
      ]),
    });
  });
});
```

---

## 📊 Success Metrics

### Before Optimization
- **CI Build Time**: ~8 minutes (full build)
- **Local Build Time**: ~3 minutes (frontend + backend)
- **Dependency Clarity**: Low (flat service directory)
- **Test Isolation**: Difficult (tightly coupled)

### After Optimization
- **CI Build Time**: ~2-4 minutes (changed modules only)
- **Local Build Time**: ~30 seconds (cached builds)
- **Dependency Clarity**: High (explicit module contracts)
- **Test Isolation**: Easy (modules can be tested independently)

### KPIs
- ✅ 50%+ reduction in CI build time
- ✅ 80%+ reduction in local rebuild time (with caching)
- ✅ Zero circular dependencies
- ✅ 100% module API documentation coverage

---

## 🗺️ Migration Strategy

### Incremental Approach (Low Risk)

**Week 1**: Backend Module Refactor
```bash
# Create new module structure
mkdir -p backend/app/modules/{auth,portfolio,trading}

# Move one service at a time
git mv backend/app/services/portfolio_optimizer.py \
        backend/app/modules/portfolio/optimizer.py

# Update imports gradually
# Run tests after each move
pytest backend/app/tests
```

**Week 2**: JavaScript Workspace Setup
```bash
# Install pnpm
npm install -g pnpm

# Create workspace
pnpm init

# Migrate packages one by one
# Start with ui-components (least risky)
```

**Week 3**: CI Change Detection
```bash
# Add paths-filter to one workflow
# Monitor for 1 week
# Roll out to remaining workflows
```

**Week 4-5**: Documentation & Testing
```bash
# Generate dependency graphs
# Write module READMEs
# Add contract tests
```

**Week 6**: Validation
```bash
# Run full test suite
# Deploy to staging
# Monitor performance metrics
```

---

## 🛠️ Recommended Tools Summary

| Category | Tool | Purpose | Priority |
|----------|------|---------|----------|
| **JavaScript PM** | pnpm | Workspace management | High |
| **Build Orchestration** | Turborepo | Caching & parallelization | High |
| **Python PM** | Poetry | Dependency management | Medium |
| **Task Runner** | Taskfile | Cross-platform task execution | Medium |
| **Dep Visualization** | pydeps, madge | Dependency graphs | Low |
| **Linting** | Ruff (Python), ESLint | Code quality | High |
| **Testing** | pytest, Jest | Unit & integration tests | High |

---

## 🚧 Risks & Mitigation

### Risk 1: Breaking Changes During Refactor
**Mitigation**:
- Move one module at a time
- Keep tests green at every step
- Use feature flags for new structure

### Risk 2: Team Onboarding
**Mitigation**:
- Create CONTRIBUTING.md with new structure
- Record loom video of new workflow
- Pair programming sessions

### Risk 3: CI Migration Downtime
**Mitigation**:
- Test on feature branch first
- Run old + new CI in parallel for 1 week
- Gradual rollout

---

## 📚 Next Steps

### Immediate Actions (This Week)
1. ✅ Review this roadmap with team
2. ✅ Set up pnpm workspace (1 hour)
3. ✅ Create one backend module (auth) as proof of concept (2 hours)
4. ✅ Add CI change detection for one workflow (1 hour)

### Short Term (Next 2 Weeks)
1. Migrate backend services to modules
2. Set up Turborepo
3. Extract ui-components package
4. Add dependency graph documentation

### Long Term (Next 1-2 Months)
1. Add tax-reporting module
2. Add planning module
3. Publish internal packages to private npm/PyPI
4. Set up remote caching

---

## 📖 References

- [Turborepo Handbook](https://turbo.build/repo/docs/handbook)
- [pnpm Workspace Guide](https://pnpm.io/workspaces)
- [Monorepo Best Practices](https://monorepo.tools/)
- [Python Monorepos with Poetry](https://python-poetry.org/docs/managing-dependencies/)
- [Module Boundaries in DDD](https://www.martinfowler.com/bliki/BoundedContext.html)

---

**Document Version**: 1.0
**Last Updated**: 2025-12-02
**Owner**: Elson Trading Platform Team
**Status**: Ready for Review
