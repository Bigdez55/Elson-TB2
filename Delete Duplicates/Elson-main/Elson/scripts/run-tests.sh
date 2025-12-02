#!/bin/bash

# Run tests for the Elson project

# Set root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Output colorization
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to run backend tests
run_backend_tests() {
    echo -e "${GREEN}Running backend tests...${NC}"
    
    cd "$ROOT_DIR/Elson/backend"
    
    # Check if python virtual environment exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Run pytest with coverage
    python -m pytest -xvs app/tests/ --cov=app --cov-report=term-missing
    
    local backend_exit_code=$?
    
    # Deactivate virtual environment if it was activated
    if [ -n "$VIRTUAL_ENV" ]; then
        deactivate
    fi
    
    return $backend_exit_code
}

# Function to run frontend tests
run_frontend_tests() {
    echo -e "${GREEN}Running frontend tests...${NC}"
    
    cd "$ROOT_DIR/Elson/frontend"
    
    # Run vitest
    npm test
    
    return $?
}

# Function to run trading engine tests
run_trading_engine_tests() {
    echo -e "${GREEN}Running trading engine tests...${NC}"
    
    cd "$ROOT_DIR/Elson/trading_engine"
    
    # Check if python virtual environment exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Run pytest with coverage
    python -m pytest -xvs tests/ --cov=engine --cov=strategies --cov-report=term-missing
    
    local engine_exit_code=$?
    
    # Deactivate virtual environment if it was activated
    if [ -n "$VIRTUAL_ENV" ]; then
        deactivate
    fi
    
    return $engine_exit_code
}

# Parse command-line arguments
if [ $# -eq 0 ]; then
    # No arguments, run all tests
    run_backend=true
    run_frontend=true
    run_trading_engine=true
else
    # Parse arguments
    run_backend=false
    run_frontend=false
    run_trading_engine=false
    
    for arg in "$@"; do
        case $arg in
            --backend|-b)
                run_backend=true
                ;;
            --frontend|-f)
                run_frontend=true
                ;;
            --trading-engine|-t)
                run_trading_engine=true
                ;;
            --all|-a)
                run_backend=true
                run_frontend=true
                run_trading_engine=true
                ;;
            --help|-h)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --backend, -b          Run backend tests"
                echo "  --frontend, -f         Run frontend tests"
                echo "  --trading-engine, -t   Run trading engine tests"
                echo "  --all, -a              Run all tests (default)"
                echo "  --help, -h             Display this help message"
                exit 0
                ;;
            *)
                echo -e "${RED}Unknown option: $arg${NC}"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
fi

# Initialize exit code
exit_code=0

# Run tests based on arguments
if [ "$run_backend" = true ]; then
    run_backend_tests
    backend_exit_code=$?
    if [ $backend_exit_code -ne 0 ]; then
        echo -e "${RED}Backend tests failed with exit code $backend_exit_code${NC}"
        exit_code=1
    fi
fi

if [ "$run_frontend" = true ]; then
    run_frontend_tests
    frontend_exit_code=$?
    if [ $frontend_exit_code -ne 0 ]; then
        echo -e "${RED}Frontend tests failed with exit code $frontend_exit_code${NC}"
        exit_code=1
    fi
fi

if [ "$run_trading_engine" = true ]; then
    run_trading_engine_tests
    engine_exit_code=$?
    if [ $engine_exit_code -ne 0 ]; then
        echo -e "${RED}Trading engine tests failed with exit code $engine_exit_code${NC}"
        exit_code=1
    fi
fi

# Final result
if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}All tests passed successfully!${NC}"
else
    echo -e "${RED}Some tests failed.${NC}"
fi

exit $exit_code