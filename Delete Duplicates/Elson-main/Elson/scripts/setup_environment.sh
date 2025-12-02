#!/bin/bash
# Setup Environment Script for Elson Wealth Platform
# This script sets up the environment for development, testing, or production

# Set default values
ENV="development"
NO_SEED=true
VENV_PATH=".venv"

# Parse command line arguments
while [ "$1" != "" ]; do
    case $1 in
        --env )     shift
                    ENV=$1
                    ;;
        --seed )    NO_SEED=false
                    ;;
        --venv )    shift
                    VENV_PATH=$1
                    ;;
        --help )    echo "Usage: ./setup_environment.sh [--env development|testing|production] [--seed] [--venv PATH]"
                    echo "  --env ENV       Set environment (development, testing, production). Default: development"
                    echo "  --seed          Seed the database with sample data"
                    echo "  --venv PATH     Path to Python virtual environment. Default: .venv"
                    exit
                    ;;
        * )         echo "Invalid argument: $1"
                    echo "Use --help for usage information"
                    exit 1
    esac
    shift
done

# Validate environment
if [[ "$ENV" != "development" && "$ENV" != "testing" && "$ENV" != "production" ]]; then
    echo "Error: Invalid environment '$ENV'. Must be one of: development, testing, production"
    exit 1
fi

# Check if we're in the correct directory
if [ ! -d "Elson" ]; then
    echo "Error: This script must be run from the project root directory containing the 'Elson' folder"
    exit 1
fi

echo "Setting up Elson Wealth Platform for $ENV environment..."

# Create .env file that points to the appropriate environment config
echo "ENVIRONMENT=$ENV" > .env
echo "Environment set to: $ENV"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_PATH" ]; then
    echo "Creating Python virtual environment at $VENV_PATH..."
    python3 -m venv "$VENV_PATH"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_PATH/bin/activate"

# Install dependencies
echo "Installing dependencies..."
cd Elson/backend
pip install -r requirements.txt

# Install development/testing dependencies if appropriate
if [ "$ENV" != "production" ]; then
    echo "Installing development dependencies..."
    pip install -r requirements-dev.txt
fi

# Initialize database
echo "Initializing database..."
if [ "$NO_SEED" = false ]; then
    echo "Seeding database with sample data..."
    python init_db.py --env $ENV --seed
else
    python init_db.py --env $ENV
fi

# Display success message
if [ "$ENV" = "development" ]; then
    echo -e "\n\033[0;32mDevelopment environment setup complete!\033[0m"
    echo "To start the development server, run:"
    echo "  cd Elson/backend"
    echo "  python start_server.py"
    
    echo -e "\nTo access the API, visit: http://127.0.0.1:8000/docs"
elif [ "$ENV" = "testing" ]; then
    echo -e "\n\033[0;32mTesting environment setup complete!\033[0m"
    echo "To run tests, run:"
    echo "  cd Elson/backend"
    echo "  pytest -v"
elif [ "$ENV" = "production" ]; then
    echo -e "\n\033[0;32mProduction environment setup complete!\033[0m"
    echo "WARNING: For production, make sure to:"
    echo "  1. Update all API keys in Elson/config/production.env"
    echo "  2. Set up proper database and Redis instances"
    echo "  3. Configure proper SSL/TLS certificates"
    echo "  4. Set up a reverse proxy (e.g., Nginx) for production"
fi

# Deactivate virtual environment
deactivate