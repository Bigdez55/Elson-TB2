# Contributing to Elson Wealth Platform

Thank you for your interest in contributing to the Elson Wealth Platform! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)

## 🚀 Development Setup

### Prerequisites

- **Python 3.12+** for backend development
- **Node.js 18+** for frontend development
- **Docker & Docker Compose** for containerized development
- **Git** with pre-commit hooks enabled

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Elson
   ```

2. **Install pre-commit hooks:**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

3. **Backend setup:**
   ```bash
   cd Elson/backend
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Frontend setup:**
   ```bash
   cd Elson/frontend
   npm install
   ```

5. **Environment configuration:**
   ```bash
   cp config/development.env.example config/development.env
   # Edit the file with your local settings
   ```

## 📁 Project Structure

```
Elson/
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── core/           # Core functionality (auth, config, etc.)
│   │   ├── models/         # SQLAlchemy models
│   │   ├── routes/         # API route definitions
│   │   ├── services/       # Business logic layer
│   │   └── tests/          # Backend tests
│   ├── alembic/            # Database migrations
│   └── requirements*.txt   # Python dependencies
├── frontend/               # React/TypeScript frontend
│   ├── src/
│   │   ├── app/            # Main application code
│   │   ├── components/     # React components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── services/       # API services
│   │   └── utils/          # Utility functions
│   └── package.json        # Node.js dependencies
├── trading_engine/         # Core trading algorithms
│   ├── ai_model_engine/    # AI/ML models
│   ├── strategies/         # Trading strategies
│   └── tests/              # Trading engine tests
├── infrastructure/         # Deployment configurations
│   ├── kubernetes/         # K8s manifests
│   └── terraform/          # Infrastructure as code
├── config/                 # Environment configurations
└── docs/                   # Documentation
```

## 🔄 Development Workflow

### Branch Strategy

- **`main`** - Production-ready code
- **`development`** - Integration branch for features
- **`feature/*`** - Individual feature branches
- **`hotfix/*`** - Emergency fixes for production
- **`release/*`** - Release preparation branches

### Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(auth): add JWT token refresh mechanism
fix(trading): resolve order execution timing issue
docs(api): update authentication endpoints documentation
```

## 📏 Coding Standards

### Backend (Python)

- **Formatting:** Black (88 character line length)
- **Import sorting:** isort with Black profile
- **Linting:** flake8 with custom rules
- **Type hints:** Required for all public functions
- **Docstrings:** Google style for all modules, classes, and functions

```python
def calculate_portfolio_value(
    positions: List[Position], 
    current_prices: Dict[str, float]
) -> Decimal:
    """Calculate total portfolio value based on current market prices.
    
    Args:
        positions: List of portfolio positions
        current_prices: Dict of symbol to current price
        
    Returns:
        Total portfolio value as Decimal
        
    Raises:
        ValueError: If price data is missing for any position
    """
    pass
```

### Frontend (TypeScript/React)

- **Formatting:** Prettier with 2-space indentation
- **Linting:** ESLint with TypeScript and React rules
- **Type safety:** Strict TypeScript configuration
- **Component structure:** Functional components with hooks
- **State management:** Redux Toolkit for global state

```typescript
interface PortfolioProps {
  userId: string;
  positions: Position[];
  onPositionUpdate?: (position: Position) => void;
}

export const Portfolio: React.FC<PortfolioProps> = ({
  userId,
  positions,
  onPositionUpdate,
}) => {
  // Component implementation
};
```

## 🧪 Testing Guidelines

### Backend Testing

- **Unit tests:** For individual functions and classes
- **Integration tests:** For API endpoints and database operations
- **Minimum coverage:** 80% line coverage required
- **Test structure:** Arrange-Act-Assert pattern

```python
def test_calculate_portfolio_value():
    # Arrange
    positions = [create_test_position("AAPL", 10, 150.0)]
    prices = {"AAPL": 155.0}
    
    # Act
    result = calculate_portfolio_value(positions, prices)
    
    # Assert
    assert result == Decimal("1550.0")
```

### Frontend Testing

- **Unit tests:** For utility functions and custom hooks
- **Component tests:** For React components using React Testing Library
- **Integration tests:** For user workflows
- **E2E tests:** For critical user paths (optional)

```typescript
test('should display portfolio value correctly', () => {
  const mockPositions = [createMockPosition('AAPL', 10, 150)];
  
  render(<Portfolio userId="test" positions={mockPositions} />);
  
  expect(screen.getByText('$1,500.00')).toBeInTheDocument();
});
```

### Running Tests

```bash
# Backend tests
cd Elson/backend
pytest app/tests/ -v --cov=app

# Frontend tests
cd Elson/frontend
npm run test

# Trading engine tests
cd Elson
python -m pytest trading_engine/tests/ -v
```

## 🔄 Pull Request Process

### Before Submitting

1. **Update from main:**
   ```bash
   git checkout main
   git pull origin main
   git checkout your-feature-branch
   git rebase main
   ```

2. **Run quality checks:**
   ```bash
   # Backend
   cd Elson/backend
   black . && isort . && flake8 . && pytest

   # Frontend
   cd Elson/frontend
   npm run lint && npm run typecheck && npm run test
   ```

3. **Update documentation** if necessary

### PR Template

When creating a PR, include:

- **Description:** What changes were made and why
- **Type of change:** Feature, bug fix, refactor, etc.
- **Testing:** How the changes were tested
- **Screenshots:** For UI changes
- **Breaking changes:** Any API or interface changes
- **Checklist:** Completed items from the PR template

### Review Process

1. **Automated checks** must pass (CI pipeline)
2. **Code review** by at least one team member
3. **Security review** for sensitive changes
4. **Manual testing** for significant features

## 🚀 Release Process

### Version Management

We use [Semantic Versioning](https://semver.org/):
- **MAJOR:** Breaking changes
- **MINOR:** New features (backward compatible)
- **PATCH:** Bug fixes (backward compatible)

### Release Steps

1. **Create release branch:**
   ```bash
   git checkout -b release/v1.2.0
   ```

2. **Update version numbers** in relevant files

3. **Update CHANGELOG.md** with release notes

4. **Create release PR** to main

5. **Tag release** after merge:
   ```bash
   git tag -a v1.2.0 -m "Release version 1.2.0"
   git push origin v1.2.0
   ```

6. **GitHub Actions** will automatically:
   - Build and push Docker images
   - Create GitHub release
   - Generate deployment package

## 🆘 Getting Help

- **Documentation:** Check the `docs/` directory
- **Issues:** Create a GitHub issue for bugs or feature requests
- **Discussions:** Use GitHub Discussions for questions
- **Code Review:** Tag relevant team members for reviews

## 📜 Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/). By participating, you agree to uphold this code.

---

Thank you for contributing to the Elson Wealth Platform! 🚀