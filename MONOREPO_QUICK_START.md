# Monorepo Optimization - Quick Start Guide

**Goal**: Get started with monorepo improvements in the next 2 hours.

**Prerequisites**: Node.js 18+, Python 3.12+, Git

---

## 🚀 Getting Started (30 minutes)

### Step 1: Install pnpm (5 minutes)

```bash
# Install pnpm globally
npm install -g pnpm@8

# Verify installation
pnpm --version  # Should show 8.x.x
```

---

### Step 2: Set Up JavaScript Workspace (10 minutes)

**Create workspace configuration:**

```bash
# From repository root
cat > pnpm-workspace.yaml << 'EOF'
packages:
  - 'frontend'
  - 'packages/*'
EOF
```

**Update root package.json:**

```bash
cat > package.json << 'EOF'
{
  "name": "elson-trading-monorepo",
  "version": "1.0.0",
  "private": true,
  "description": "Elson Trading Platform Monorepo",
  "scripts": {
    "dev": "pnpm --filter web dev",
    "build": "pnpm -r build",
    "test": "pnpm -r test",
    "lint": "pnpm -r lint",
    "clean": "pnpm -r clean && rm -rf node_modules"
  },
  "devDependencies": {
    "turbo": "^1.11.0"
  },
  "engines": {
    "node": ">=18.0.0",
    "pnpm": ">=8.0.0"
  }
}
EOF
```

**Install pnpm and dependencies:**

```bash
# Install root dependencies
pnpm install

# Install all workspace dependencies
pnpm install -r
```

---

### Step 3: Install Turborepo (5 minutes)

```bash
# Install Turbo
pnpm add turbo -D -w

# Create turbo.json configuration
cat > turbo.json << 'EOF'
{
  "$schema": "https://turbo.build/schema.json",
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", "build/**", ".next/**"],
      "env": ["NODE_ENV"]
    },
    "test": {
      "dependsOn": ["build"],
      "outputs": ["coverage/**"],
      "cache": true
    },
    "lint": {
      "outputs": [],
      "cache": true
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "clean": {
      "cache": false
    }
  },
  "globalDependencies": [
    "tsconfig.json",
    ".env"
  ]
}
EOF
```

**Update scripts to use Turbo:**

```bash
# Update package.json scripts
cat > package.json << 'EOF'
{
  "name": "elson-trading-monorepo",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "turbo run dev",
    "build": "turbo run build",
    "test": "turbo run test",
    "lint": "turbo run lint",
    "clean": "turbo run clean && rm -rf node_modules"
  },
  "devDependencies": {
    "turbo": "^1.11.0"
  },
  "engines": {
    "node": ">=18.0.0",
    "pnpm": ">=8.0.0"
  }
}
EOF
```

---

### Step 4: Test the Setup (10 minutes)

```bash
# Test build with caching
pnpm build

# Build again (should use cache - instant!)
pnpm build

# Run dev server
pnpm dev

# View dependency graph
pnpm turbo run build --graph
```

**Expected Output**:
```
✓ web:build: cache hit, replaying output [2.3s]
```

---

## 🏗️ Next Steps: Refactor Backend Module (1 hour)

### Step 1: Create Auth Module Structure

```bash
# Create auth module directory
mkdir -p backend/app/modules/auth

# Create module files
touch backend/app/modules/auth/__init__.py
touch backend/app/modules/auth/service.py
touch backend/app/modules/auth/models.py
touch backend/app/modules/auth/schemas.py
touch backend/app/modules/auth/repository.py
```

---

### Step 2: Move Existing Code

**Example: Extract auth service**

```python
# backend/app/modules/auth/service.py
"""
Authentication Service

Handles user registration, login, and JWT token management.
"""

from datetime import timedelta
from typing import Optional

from app.core.config import settings
from app.modules.auth.models import User
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import UserCreate, Token
from app.shared.security import create_access_token, verify_password, hash_password


class AuthService:
    """Authentication business logic."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register_user(self, user_create: UserCreate) -> User:
        """Register a new user."""
        # Check if user exists
        existing_user = await self.user_repo.get_by_email(user_create.email)
        if existing_user:
            raise ValueError("User already exists")

        # Hash password
        hashed_password = hash_password(user_create.password)

        # Create user
        user = await self.user_repo.create(
            email=user_create.email,
            hashed_password=hashed_password,
            full_name=user_create.full_name,
        )

        return user

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate user credentials."""
        user = await self.user_repo.get_by_email(email)
        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user

    def create_token(self, user_id: int) -> Token:
        """Create JWT access token."""
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user_id)},
            expires_delta=access_token_expires,
        )
        return Token(access_token=access_token, token_type="bearer")
```

**Repository layer:**

```python
# backend/app/modules/auth/repository.py
"""
User Repository

Database access layer for User model.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.modules.auth.models import User


class UserRepository:
    """User database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        email: str,
        hashed_password: str,
        full_name: str,
    ) -> User:
        """Create a new user."""
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
```

**Module export:**

```python
# backend/app/modules/auth/__init__.py
"""
Auth Module

Public API for authentication.
"""

from .service import AuthService
from .repository import UserRepository
from .models import User
from .schemas import UserCreate, UserLogin, Token

__all__ = [
    "AuthService",
    "UserRepository",
    "User",
    "UserCreate",
    "UserLogin",
    "Token",
]
```

---

### Step 3: Update Imports in Endpoints

```python
# backend/app/api/api_v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth import AuthService, UserRepository, UserCreate, UserLogin

router = APIRouter()


@router.post("/register")
async def register(
    user_create: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user."""
    repo = UserRepository(db)
    service = AuthService(repo)

    try:
        user = await service.register_user(user_create)
        return {"id": user.id, "email": user.email}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(
    user_login: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """Login and get access token."""
    repo = UserRepository(db)
    service = AuthService(repo)

    user = await service.authenticate(user_login.email, user_login.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = service.create_token(user.id)
    return token
```

---

### Step 4: Test the Refactored Module

```bash
# Run backend tests
cd backend
pytest app/tests/modules/test_auth_module.py -v

# Test imports
python -c "from app.modules.auth import AuthService; print('✅ Auth module works!')"

# Run full test suite
pytest app/tests -v
```

---

## 🔍 Verify Module Isolation

**Check dependencies:**

```bash
# Install pydeps
pip install pydeps

# Generate dependency graph
cd backend
pydeps app/modules/auth --max-bacon=2 -o ../../docs/auth-module-deps.svg

# Check for circular dependencies
pydeps app/modules --max-bacon=3 --show-cycles
```

**Expected Output**: No circular dependencies

---

## 📊 CI Change Detection Setup (30 minutes)

### Update GitHub Actions Workflow

```bash
# Create new workflow file
cat > .github/workflows/ci-optimized.yml << 'EOF'
name: CI Optimized

on:
  push:
    branches: [main, develop, 'claude/**']
  pull_request:

jobs:
  # Detect changed paths
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
              - 'requirements.txt'
              - 'Dockerfile'
            frontend:
              - 'frontend/**'
              - 'pnpm-workspace.yaml'
              - 'turbo.json'
            packages:
              - 'packages/**'

  # Backend CI (only if backend changed)
  backend-ci:
    needs: changes
    if: needs.changes.outputs.backend == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
          cache: 'pip'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r ../requirements.txt
      - name: Run tests
        run: |
          cd backend
          pytest app/tests --cov --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml

  # Frontend CI (only if frontend changed)
  frontend-ci:
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
      - name: Lint
        run: pnpm turbo run lint
      - name: Build
        run: pnpm turbo run build
      - name: Test
        run: pnpm turbo run test

  # Security scan (always run)
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Trivy scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          severity: 'CRITICAL,HIGH'
EOF
```

---

## 📈 Measure Performance Improvements

### Before Optimization

```bash
# Time full build
time (cd backend && pytest app/tests)
# ~180 seconds

time (cd frontend && npm run build)
# ~120 seconds

# Total: ~5 minutes
```

### After Optimization (with caching)

```bash
# First build (cold cache)
time pnpm turbo run build
# ~120 seconds

# Second build (warm cache)
time pnpm turbo run build
# ~2 seconds (98% faster!)

# Changed only backend
time pnpm turbo run test --filter=backend
# ~30 seconds (skips frontend)
```

---

## 🎯 Success Checklist

- [ ] pnpm installed and working
- [ ] Turborepo configured with caching
- [ ] First backend module (auth) refactored
- [ ] Module isolation verified (no circular deps)
- [ ] CI change detection implemented
- [ ] Build times measured (before/after)
- [ ] Documentation updated (ARCHITECTURE.md)

---

## 🚨 Troubleshooting

### Issue: "pnpm not found"
```bash
# Fix: Install pnpm globally
npm install -g pnpm@8

# Or use npx
npx pnpm install
```

### Issue: "Module not found after refactor"
```bash
# Fix: Check __init__.py exports
cat backend/app/modules/auth/__init__.py

# Verify Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
```

### Issue: "Turbo cache not working"
```bash
# Fix: Clear cache and rebuild
pnpm turbo run build --force

# Check cache location
pnpm turbo run build --summarize
```

---

## 📚 Next Actions

1. **Complete Backend Refactor**
   - [ ] Auth module (done above)
   - [ ] Portfolio module
   - [ ] Trading module
   - [ ] Market data module

2. **Extract Frontend Packages**
   - [ ] API client package
   - [ ] Types package
   - [ ] UI components package

3. **Add Future Modules**
   - [ ] Tax reporting
   - [ ] Financial planning
   - [ ] Compliance checking

4. **Set Up Remote Caching**
   - [ ] Sign up for Vercel
   - [ ] Configure Turbo remote cache
   - [ ] Share cache across team

---

**Estimated Time to Complete**: 2 hours
**Difficulty**: Medium
**Impact**: High (50%+ build time reduction)

Ready to get started? Follow the steps above and you'll have a production-grade monorepo setup in no time! 🚀
