# Elson Trading Platform - Complete Setup Guide

This guide will walk you through setting up the Elson Trading Platform from scratch to a fully functional development or production environment.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (Development)](#quick-start-development)
3. [Detailed Setup](#detailed-setup)
4. [Docker Setup](#docker-setup)
5. [Production Deployment](#production-deployment)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Python 3.12+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Git** - [Download](https://git-scm.com/)

### Optional but Recommended

- **Docker** - [Download](https://www.docker.com/get-started)
- **Redis** - For caching (can run via Docker)
- **PostgreSQL** - For production database

### Required API Keys

You'll need to sign up for these free services:

1. **Alpha Vantage** (Market Data)
   - Sign up: https://www.alphavantage.co/support/#api-key
   - Free tier: 5 API calls per minute, 500 per day
   - Time to get: ~1 minute

2. **Alpaca** (Paper Trading)
   - Sign up: https://alpaca.markets/
   - Paper trading is completely FREE
   - No money required
   - Time to get: ~5 minutes

3. **Polygon.io** (Optional - Real-time Data)
   - Sign up: https://polygon.io/
   - Free tier available
   - Time to get: ~2 minutes

---

## Quick Start (Development)

Get up and running in 5 minutes:

```bash
# 1. Clone the repository (if not already done)
git clone https://github.com/Bigdez55/Elson-TB2.git
cd Elson-TB2

# 2. Configure environment variables
# The .env file has been created for you
# Edit it and add your API keys:
nano .env  # or use any text editor

# REQUIRED: Update these values in .env:
# - SECRET_KEY (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
# - ALPHA_VANTAGE_API_KEY
# - ALPACA_API_KEY
# - ALPACA_SECRET_KEY

# 3. Set up the backend
pip install -r requirements.txt

# 4. Set up the frontend
cd frontend
npm install
cd ..

# 5. Start Redis (optional, for caching)
docker run -d -p 6379:6379 --name elson-redis redis:7-alpine

# 6. Start the backend
cd backend
python -m uvicorn app.main:app --reload --port 8000 &
cd ..

# 7. Start the frontend
cd frontend
npm start
```

**Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Detailed Setup

### Step 1: Environment Configuration

#### Generate a Secure Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and paste it as your `SECRET_KEY` in `.env`.

#### Get Your API Keys

1. **Alpha Vantage:**
   ```
   1. Visit: https://www.alphavantage.co/support/#api-key
   2. Enter your email
   3. Copy the API key
   4. Paste it as ALPHA_VANTAGE_API_KEY in .env
   ```

2. **Alpaca (Paper Trading):**
   ```
   1. Visit: https://alpaca.markets/
   2. Click "Start Paper Trading" (it's free!)
   3. Create an account
   4. Go to Dashboard → API Keys
   5. Generate new API key
   6. Copy both Key and Secret
   7. Paste them in .env as:
      - ALPACA_API_KEY
      - ALPACA_SECRET_KEY
   ```

3. **Polygon (Optional):**
   ```
   1. Visit: https://polygon.io/
   2. Sign up for free tier
   3. Copy API key
   4. Paste as POLYGON_API_KEY in .env
   ```

#### Edit .env File

```bash
nano .env
```

**Minimum required changes:**
```env
SECRET_KEY=<your-generated-secret-key>
ALPHA_VANTAGE_API_KEY=<your-alpha-vantage-key>
ALPACA_API_KEY=<your-alpaca-key>
ALPACA_SECRET_KEY=<your-alpaca-secret>
```

### Step 2: Backend Setup

#### Install Python Dependencies

```bash
# For full development environment (includes AI/ML features)
pip install -r requirements.txt

# OR for minimal setup (faster, smaller)
pip install -r requirements-docker.txt
```

#### Install System Dependencies (if needed)

Some packages like TA-Lib may require system libraries:

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y build-essential libta-lib0-dev
```

**macOS:**
```bash
brew install ta-lib
```

**Windows:**
Download pre-built wheels from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib

#### Initialize the Database

The database will be automatically initialized on first run. Just start the backend:

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Starting Elson Trading Platform
INFO:     Application startup complete.
```

**For production:** Set up proper migrations:
```bash
# Initialize Alembic
cd backend
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

### Step 3: Frontend Setup

#### Install Node Dependencies

```bash
cd frontend
npm install
```

This will install:
- React and React Router
- Redux Toolkit for state management
- Axios for API calls
- Tailwind CSS for styling
- TypeScript and testing libraries

#### Start Development Server

```bash
npm start
```

The frontend will open automatically at http://localhost:3000.

### Step 4: Verify Setup

1. **Backend Health Check:**
   ```bash
   curl http://localhost:8000/health
   ```
   Should return: `{"status":"healthy","service":"elson-trading-platform"}`

2. **API Documentation:**
   Visit http://localhost:8000/docs to see interactive API documentation.

3. **Frontend:**
   Open http://localhost:3000 - you should see the login page.

4. **Create Test Account:**
   - Click "Register"
   - Fill in the form
   - Login with your new account

---

## Docker Setup

### Using Docker Compose (Recommended for Development)

```bash
# Start all services
docker-compose up --build

# Access the application
# Backend: http://localhost:8080
# Frontend: Add frontend service to docker-compose.yml (currently commented)
```

### Building Individual Containers

**Backend:**
```bash
docker build -t elson-trading-backend:latest .
docker run -p 8080:8080 \
  -e SECRET_KEY=your-secret-key \
  -e ALPHA_VANTAGE_API_KEY=your-key \
  -e ALPACA_API_KEY=your-key \
  -e ALPACA_SECRET_KEY=your-secret \
  elson-trading-backend:latest
```

**Frontend:**
```bash
cd frontend
docker build -t elson-trading-frontend:latest .
docker run -p 80:80 elson-trading-frontend:latest
```

### Docker Compose with Frontend

To enable the frontend in Docker Compose, edit `docker-compose.yml` and uncomment the frontend service:

```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile
  ports:
    - "3000:80"
  environment:
    - REACT_APP_API_URL=http://localhost:8080/api/v1
  depends_on:
    - backend
```

Then run:
```bash
docker-compose up --build
```

---

## Production Deployment

### Option 1: Google Cloud Run (Recommended)

#### Prerequisites
- Google Cloud account
- `gcloud` CLI installed: https://cloud.google.com/sdk/docs/install

#### Setup Google Cloud

```bash
# Login to Google Cloud
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

#### Create Service Account

```bash
# Create service account for deployments
gcloud iam service-accounts create elson-deployer \
  --display-name="Elson Trading Deployer"

# Grant necessary roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:elson-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:elson-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:elson-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Create key for GitHub Actions
gcloud iam service-accounts keys create key.json \
  --iam-account=elson-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

#### Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:
```
GCP_SA_KEY: <contents of key.json file>
GCP_PROJECT_ID: your-project-id
SECRET_KEY: <your-production-secret-key>
ALPHA_VANTAGE_API_KEY: <your-key>
POLYGON_API_KEY: <your-key>
ALPACA_API_KEY: <your-key>
ALPACA_SECRET_KEY: <your-secret>
```

#### Manual Deployment

```bash
# Build and deploy using Cloud Build
gcloud builds submit --config cloudbuild.yaml

# Get the service URL
gcloud run services describe elson-trading-platform \
  --region=us-central1 \
  --format='value(status.url)'
```

#### Automated Deployment

Push to the `main` branch and GitHub Actions will automatically:
1. Run tests
2. Run security scans
3. Build Docker image
4. Deploy to Cloud Run

### Option 2: AWS/Azure/Other Cloud Providers

The application is containerized and can be deployed to any cloud provider that supports Docker containers:

- **AWS:** Elastic Container Service (ECS) or App Runner
- **Azure:** Container Instances or App Service
- **DigitalOcean:** App Platform
- **Heroku:** Container Registry

Refer to your cloud provider's documentation for container deployment.

### Production Environment Variables

Update `.env` or cloud environment variables:

```env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<strong-production-secret>
DATABASE_URL=postgresql://user:password@host:5432/dbname
ALLOWED_ORIGINS=https://yourdomain.com
ALLOWED_HOSTS=yourdomain.com
```

### Production Database

For production, use PostgreSQL instead of SQLite:

```bash
# Create PostgreSQL database
# Option 1: Google Cloud SQL
gcloud sql instances create elson-trading-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Option 2: Use managed PostgreSQL from your cloud provider
# Option 3: Self-hosted PostgreSQL

# Update DATABASE_URL in environment variables
DATABASE_URL=postgresql://username:password@host:5432/elson_trading
```

---

## Troubleshooting

### Backend Won't Start

**Error: `ModuleNotFoundError: No module named 'structlog'`**
```bash
# Install dependencies
pip install -r requirements.txt
```

**Error: `SECRET_KEY` not set**
```bash
# Generate and set SECRET_KEY in .env
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy output to .env
```

**Error: Database connection failed**
```bash
# Check DATABASE_URL in .env
# For SQLite, ensure the directory is writable
# For PostgreSQL, verify connection string
```

### Frontend Won't Start

**Error: `Cannot find module 'tailwindcss'`**
```bash
cd frontend
npm install
```

**Error: `Proxy error` when calling API**
```bash
# Ensure backend is running on port 8080
# Check package.json "proxy": "http://localhost:8080"
```

### API Key Issues

**Error: `Invalid API key`**
- Verify API keys in `.env` are correct
- Check for extra spaces or quotes
- Regenerate keys if necessary

**Rate Limit Errors**
- Alpha Vantage free tier: 5 calls/minute
- Use Polygon.io as backup
- Consider upgrading API plan

### Docker Issues

**Build fails**
```bash
# Clear Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

**Container exits immediately**
```bash
# Check logs
docker logs <container-id>

# Verify environment variables
docker-compose config
```

### Database Issues

**Tables not created**
```bash
# Backend auto-creates tables on startup
# Check backend logs for errors
# Manually create with Alembic:
cd backend
alembic upgrade head
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app.main:app --reload --port 8001
```

---

## Next Steps

Once your setup is complete:

1. **Read the Documentation:**
   - `README.md` - Overview and features
   - `SECURITY.md` - Security best practices
   - `INTEGRATION_SUMMARY.md` - Component integration guide

2. **Explore the API:**
   - Visit http://localhost:8000/docs
   - Try creating a portfolio
   - Place a paper trade
   - View market data

3. **Test Paper Trading:**
   - Create an account
   - Add cash to your portfolio
   - Search for stocks
   - Place test orders

4. **Customize:**
   - Modify Tailwind theme in `frontend/tailwind.config.js`
   - Add custom trading strategies in `backend/app/trading_engine/strategies/`
   - Integrate additional data providers

5. **Deploy:**
   - Follow the production deployment guide
   - Set up monitoring
   - Configure backups
   - Enable SSL/HTTPS

---

## Getting Help

- **Issues:** https://github.com/Bigdez55/Elson-TB2/issues
- **Documentation:** Check the `/docs` folder
- **API Reference:** http://localhost:8000/docs (when backend is running)

---

## Security Reminders

- ✅ Never commit `.env` to git (already in `.gitignore`)
- ✅ Use strong, unique `SECRET_KEY` in production
- ✅ Start with paper trading, not live trading
- ✅ Enable HTTPS in production
- ✅ Regularly update dependencies
- ✅ Review security scans in GitHub Actions
- ✅ Use environment-specific configurations

---

**Happy Trading! 📈**

Remember: This is a trading platform for educational purposes. Always use paper trading to test strategies before risking real money.
