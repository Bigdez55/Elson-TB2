# Elson Wealth Trading Platform
# Makefile for common development tasks

.PHONY: help setup-dev start-dev stop-dev test lint format clean beta-launch beta-docker beta-test docs

# Default target when running 'make' without arguments
help:
	@echo "Elson Wealth Trading Platform - Development Commands"
	@echo "--------------------------------------------------"
	@echo "Available commands:"
	@echo "  make setup-dev    : Install development dependencies"
	@echo "  make start-dev    : Start development environment"
	@echo "  make stop-dev     : Stop development environment"
	@echo "  make test         : Run all tests"
	@echo "  make test-backend : Run backend tests"
	@echo "  make test-frontend: Run frontend tests"
	@echo "  make lint         : Run linting"
	@echo "  make format       : Format code"
	@echo "  make clean        : Clean up temporary files"
	@echo "  make beta-launch  : Launch beta test suite"
	@echo "  make beta-docker  : Start beta Docker environment"
	@echo "  make beta-test    : Run beta test suite in Docker"
	@echo "  make docs         : Generate documentation"

# Setup development environment
setup-dev:
	@echo "Setting up development environment..."
	@cd Elson/backend && pip install -r requirements.txt && pip install -r requirements-dev.txt
	@cd Elson/frontend && npm install
	@echo "Development environment setup complete!"

# Start development environment
start-dev:
	@echo "Starting development environment..."
	@bash Elson/scripts/start-dev.sh

# Stop development environment
stop-dev:
	@echo "Stopping development environment..."
	@docker-compose down

# Run all tests
test: test-backend test-frontend
	@echo "All tests completed"

# Run backend tests
test-backend:
	@echo "Running backend tests..."
	@cd Elson/backend && python -m pytest
	@cd Elson/trading_engine && python -m pytest

# Run frontend tests
test-frontend:
	@echo "Running frontend tests..."
	@cd Elson/frontend && npm test

# Run linting
lint:
	@echo "Running linting..."
	@cd Elson/backend && flake8
	@cd Elson/frontend && npm run lint

# Format code
format:
	@echo "Formatting code..."
	@cd Elson/backend && black .
	@cd Elson/frontend && npm run format

# Clean up temporary files
clean:
	@echo "Cleaning up temporary files..."
	@find . -type d -name __pycache__ -exec rm -r {} +
	@find . -type d -name .pytest_cache -exec rm -r {} +
	@find . -type d -name node_modules -exec rm -r {} +
	@find . -type f -name "*.pyc" -delete
	@echo "Cleanup complete!"

# Launch beta test suite
beta-launch:
	@echo "Launching beta test suite..."
	@bash ./beta-release-setup/launch-beta-test.sh

# Start beta Docker environment
beta-docker:
	@echo "Starting beta Docker environment..."
	@docker-compose -f docker-compose.beta.yml up -d
	@echo "Beta environment started! Access at:"
	@echo "- Frontend: http://localhost:3000"
	@echo "- API Documentation: http://localhost:8000/docs"
	@echo "- Monitoring Dashboard: http://localhost:3030 (admin/elsonbeta)"
	@echo "- Feedback System: http://localhost:8080"

# Run beta test suite in Docker
beta-test:
	@echo "Running beta test suite in Docker..."
	@docker-compose -f docker-compose.beta.yml run --rm trading_engine bash -c "cd /app && python -m pytest"

# Generate documentation
docs:
	@echo "Generating documentation..."
	@cd Elson/docs && mkdocs build
	@echo "Documentation generated!"

# Run Cypress e2e tests
e2e:
	@echo "Running end-to-end tests..."
	@cd Elson/frontend && npm run cypress:run

# Code coverage report
coverage:
	@echo "Generating code coverage report..."
	@cd Elson/backend && python -m pytest --cov=app --cov-report=html
	@cd Elson/frontend && npm run test:coverage
	@echo "Coverage reports generated!"

# Vulnerability scan
security-scan:
	@echo "Running security scan..."
	@cd Elson/backend && bandit -r app
	@cd Elson/frontend && npm audit
	@echo "Security scan complete!"