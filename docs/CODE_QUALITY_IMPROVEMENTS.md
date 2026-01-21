# Code Quality Improvement Suggestions

This document outlines recommended improvements identified during the linting and testing audit performed on 2026-01-21.

## Current Status

### Backend
- **Linting:** `black` and `isort` auto-formatted 157+ Python files
- **Tests:** 52 passed, 2 skipped, 16 xfailed (expected failures)
- **Warnings:** 148 deprecation warnings (mostly `datetime.utcnow()`)

### Frontend
- **Linting:** 0 errors, 140 warnings (unused variables)
- **TypeScript:** No type errors
- **Tests:** 209 passed, 137 skipped, 6 test suites skipped

---

## Recommended Improvements

### 1. Add Pre-commit Hooks for Automatic Linting

**Priority:** High
**Effort:** Low
**Why:** Prevents lint errors from being committed, ensuring code quality at commit time.

#### Implementation

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml in repository root
```

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        args: [--line-length=88]

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: [--profile=black]

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203]

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.56.0
    hooks:
      - id: eslint
        files: \.[jt]sx?$
        types: [file]
        additional_dependencies:
          - eslint@8.56.0
          - typescript
          - '@typescript-eslint/parser'
          - '@typescript-eslint/eslint-plugin'
```

```bash
# Install hooks
pre-commit install

# Run on all files (optional)
pre-commit run --all-files
```

---

### 2. Fix Deprecated `datetime.utcnow()` Calls

**Priority:** High
**Effort:** Medium
**Why:** Python 3.12+ will remove `datetime.utcnow()`. Currently generates 148 deprecation warnings.

#### Files Affected

| File | Line Count |
|------|------------|
| `app/services/paper_trading.py` | 2 |
| `app/services/broker/paper.py` | 4 |
| `tests/integration/test_paper_trading.py` | 5 |

#### Fix Pattern

Replace:
```python
from datetime import datetime

# Old (deprecated)
timestamp = datetime.utcnow()
```

With:
```python
from datetime import datetime, timezone

# New (timezone-aware)
timestamp = datetime.now(timezone.utc)
```

#### Automated Fix Script

```bash
# Run from backend directory
find . -name "*.py" -exec sed -i 's/datetime\.utcnow()/datetime.now(timezone.utc)/g' {} \;

# Then manually add timezone import where needed
```

---

### 3. Clean Up Unused Variables and Imports

**Priority:** Medium
**Effort:** Low
**Why:** 140 ESLint warnings (frontend) and 433+ flake8 warnings (backend) for unused code.

#### Backend Auto-fix

```bash
# Install autoflake
pip install autoflake

# Remove unused imports
autoflake --in-place --remove-all-unused-imports --recursive app/

# Remove unused variables
autoflake --in-place --remove-unused-variables --recursive app/
```

#### Frontend Fix Pattern

For intentionally unused variables, prefix with underscore:

```typescript
// Instead of:
const { unused, used } = someObject;

// Use:
const { unused: _unused, used } = someObject;
// Or simply omit if not needed
```

#### Key Frontend Files with Warnings

| File | Warning Count |
|------|---------------|
| `src/components/portfolio/PortfolioBuilder.tsx` | 8 |
| `src/components/portfolio/PortfolioPerformance.tsx` | 10 |
| `src/pages/HomePage.tsx` | 9 |
| `src/pages/SettingsPage.tsx` | 4 |

---

### 4. Refactor Skipped Test Suites

**Priority:** Medium
**Effort:** High
**Why:** 6 test suites are skipped, reducing test coverage significantly.

#### Skipped Test Files

| File | Issue |
|------|-------|
| `OrderForm.test.tsx` | Needs Redux Provider setup |
| `TradeHistory.test.tsx` | Needs Redux Provider setup |
| `EnhancedOrderForm.test.tsx` | Needs complete provider chain |
| `LiveQuoteDisplay.test.tsx` | WebSocket mock issues |
| `useMarketWebSocket.test.ts` | WebSocket mock cleanup |
| `TradingFlow.e2e.test.tsx` | Complex e2e infrastructure |

#### Recommended Solution: Create Shared Test Utilities

Create `src/test-utils/renderWithProviders.tsx`:

```typescript
import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { Provider } from 'react-redux';
import { MemoryRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import { TradingContextProvider } from '../contexts/TradingContext';
import { authSlice } from '../store/slices/authSlice';
import { tradingSlice } from '../store/slices/tradingSlice';

interface ExtendedRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  preloadedState?: Record<string, unknown>;
  route?: string;
}

export function renderWithProviders(
  ui: ReactElement,
  {
    preloadedState = {},
    route = '/',
    ...renderOptions
  }: ExtendedRenderOptions = {}
) {
  const store = configureStore({
    reducer: {
      auth: authSlice.reducer,
      trading: tradingSlice.reducer,
    },
    preloadedState,
  });

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <Provider store={store}>
        <MemoryRouter initialEntries={[route]}>
          <TradingContextProvider>
            {children}
          </TradingContextProvider>
        </MemoryRouter>
      </Provider>
    );
  }

  return { store, ...render(ui, { wrapper: Wrapper, ...renderOptions }) };
}

export * from '@testing-library/react';
```

Usage:
```typescript
import { renderWithProviders, screen } from '../test-utils/renderWithProviders';
import OrderForm from './OrderForm';

test('renders order form', () => {
  renderWithProviders(<OrderForm />);
  expect(screen.getByRole('form')).toBeInTheDocument();
});
```

---

### 5. Fix xfailed Backend Tests

**Priority:** Medium
**Effort:** Medium
**Why:** 16 tests are marked as xfail (expected to fail), indicating incomplete implementations.

#### Tests Needing Refactoring

| Test File | Issue |
|-----------|-------|
| `test_trading_pipeline.py` | TradingService API changed - dependency injection mismatch |
| `test_paper_trading_flow.py` | Missing fixtures (owner_id, test user) |

#### Fix for `test_trading_pipeline.py`

The tests expect TradingService to accept dependency injection:
```python
trading_service = TradingService(
    db=mock_db_session,
    market_data_service=mock_market_data,
    risk_service=mock_risk_service,
    trade_executor=mock_executor,
    circuit_breaker=mock_circuit_breaker,
)
```

But the actual implementation creates dependencies internally. Options:
1. Refactor TradingService to support dependency injection
2. Use `unittest.mock.patch` to mock internal dependencies
3. Convert to integration tests with real dependencies

#### Fix for `test_paper_trading_flow.py`

Add proper fixtures:
```python
@pytest.fixture
def test_user(db_session):
    """Create a test user with proper owner_id."""
    user = User(
        email="test@example.com",
        hashed_password="hashed",
        full_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def test_portfolio(db_session, test_user):
    """Create a test portfolio with owner_id."""
    portfolio = Portfolio(
        user_id=test_user.id,
        owner_id=test_user.id,  # Required field
        name="Test Portfolio",
        cash_balance=10000.0,
    )
    db_session.add(portfolio)
    db_session.commit()
    return portfolio
```

---

### 6. Add CI Pipeline Checks

**Priority:** High
**Effort:** Medium
**Why:** Automate lint and test validation on every PR.

#### GitHub Actions Workflow

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-lint:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
      - run: pip install -r requirements.txt
      - run: pip install black isort flake8
      - run: black --check app/
      - run: isort --check-only app/ --profile black
      - run: flake8 app/ --max-line-length=88 --extend-ignore=E203

  backend-test:
    runs-on: ubuntu-latest
    needs: backend-lint
    defaults:
      run:
        working-directory: backend
    services:
      redis:
        image: redis:7
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --tb=short
        env:
          REDIS_URL: redis://localhost:6379

  frontend-lint:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      - run: npm ci
      - run: npm run lint
      - run: npx tsc --noEmit

  frontend-test:
    runs-on: ubuntu-latest
    needs: frontend-lint
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      - run: npm ci
      - run: CI=true npm test -- --watchAll=false --coverage
```

---

## Implementation Priority

| Priority | Task | Effort | Impact |
|----------|------|--------|--------|
| 1 | Add CI Pipeline | Medium | High - Catches issues before merge |
| 2 | Pre-commit Hooks | Low | High - Prevents bad commits |
| 3 | Fix datetime.utcnow() | Medium | Medium - Future compatibility |
| 4 | Clean Unused Code | Low | Low - Code cleanliness |
| 5 | Refactor Skipped Tests | High | Medium - Better coverage |
| 6 | Fix xfailed Tests | Medium | Medium - More reliable tests |

---

## Metrics to Track

After implementing these improvements, track:

1. **Lint Error Count:** Target 0 errors, <50 warnings
2. **Test Coverage:** Target >80% for critical paths
3. **CI Pass Rate:** Target >95% on first run
4. **Deprecation Warnings:** Target 0

---

*Document generated: 2026-01-21*
*Last audit: Linting and testing audit*
