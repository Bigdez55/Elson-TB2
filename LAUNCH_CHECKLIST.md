# Elson Trading Platform - Launch Checklist

Use this checklist to ensure your platform is properly configured before launch.

## ✅ Pre-Launch Checklist

### 1. Environment Configuration

- [ ] `.env` file created (✓ Already done)
- [ ] `SECRET_KEY` is a strong, random value (min 32 characters)
  ```bash
  # Generate with:
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- [ ] `ALPHA_VANTAGE_API_KEY` added
- [ ] `ALPACA_API_KEY` added
- [ ] `ALPACA_SECRET_KEY` added
- [ ] `DATABASE_URL` configured correctly
- [ ] `ENVIRONMENT` set to appropriate value (`development` or `production`)

### 2. Dependencies Installation

**Backend:**
- [ ] Python 3.12+ installed
- [ ] Backend dependencies installed
  ```bash
  pip install -r requirements.txt
  ```
- [ ] System dependencies installed (TA-Lib, etc.)

**Frontend:**
- [ ] Node.js 18+ installed
- [ ] Frontend dependencies installed
  ```bash
  cd frontend && npm install
  ```

### 3. Configuration Files

**All Created! ✓**
- [x] `.dockerignore` created
- [x] `.gcloudignore` created
- [x] `frontend/tailwind.config.js` created
- [x] `frontend/postcss.config.js` created
- [x] `frontend/Dockerfile` created
- [x] `frontend/nginx.conf` created
- [x] `LICENSE` created
- [x] `SETUP_GUIDE.md` created

### 4. Database Setup

- [ ] Database initialized
  ```bash
  # Auto-initializes on first backend start
  cd backend
  python -m uvicorn app.main:app --reload
  ```

**For Production (Recommended):**
- [ ] PostgreSQL database created
- [ ] Alembic migrations initialized
  ```bash
  cd backend
  alembic init alembic
  alembic revision --autogenerate -m "Initial migration"
  alembic upgrade head
  ```

### 5. Services Running

**Development:**
- [ ] Redis running (optional but recommended)
  ```bash
  docker run -d -p 6379:6379 --name elson-redis redis:7-alpine
  ```
- [ ] Backend running
  ```bash
  cd backend
  python -m uvicorn app.main:app --reload --port 8000
  ```
- [ ] Frontend running
  ```bash
  cd frontend
  npm start
  ```

**Production:**
- [ ] Docker containers built
- [ ] Services deployed to cloud
- [ ] Health checks passing

### 6. Verification

- [ ] Backend health check passes
  ```bash
  curl http://localhost:8000/health
  # Should return: {"status":"healthy","service":"elson-trading-platform"}
  ```
- [ ] API documentation accessible at http://localhost:8000/docs
- [ ] Frontend loads at http://localhost:3000
- [ ] Can create a user account
- [ ] Can login successfully
- [ ] API calls from frontend work

### 7. Security Checks

- [ ] `.env` is in `.gitignore` (already done ✓)
- [ ] `SECRET_KEY` is unique and not the default value
- [ ] Using paper trading URL for Alpaca (not live trading)
- [ ] CORS origins configured correctly
- [ ] Rate limiting configured
- [ ] HTTPS enabled (production only)

### 8. API Keys Validation

Test each API key:

**Alpha Vantage:**
```bash
curl "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=IBM&apikey=YOUR_KEY"
```

**Alpaca:**
- [ ] Can connect to paper trading API
- [ ] Account info retrieved successfully

### 9. Production Deployment (Cloud Run)

If deploying to Google Cloud Run:

- [ ] GCP project created
- [ ] Service account created with proper roles
- [ ] GitHub secrets configured:
  - `GCP_SA_KEY`
  - `GCP_PROJECT_ID`
  - `SECRET_KEY`
  - `ALPHA_VANTAGE_API_KEY`
  - `ALPACA_API_KEY`
  - `ALPACA_SECRET_KEY`
- [ ] Cloud Build API enabled
- [ ] Cloud Run API enabled
- [ ] Container Registry API enabled
- [ ] Deployment successful
- [ ] Custom domain configured (optional)
- [ ] SSL certificate configured

### 10. Testing

**Backend Tests:**
```bash
cd backend
pytest --cov=app --cov-report=html
```
- [ ] Backend tests passing
- [ ] Code coverage > 70%

**Frontend Tests:**
```bash
cd frontend
npm test -- --coverage --watchAll=false
```
- [ ] Frontend tests passing
- [ ] No TypeScript errors
- [ ] Build succeeds

### 11. Monitoring & Logging

- [ ] Logging configured and working
- [ ] Error tracking set up (Sentry recommended)
- [ ] Metrics collection enabled (optional)
- [ ] Alerts configured (production)

### 12. Documentation

- [ ] README.md reviewed and accurate
- [ ] SETUP_GUIDE.md followed successfully
- [ ] API endpoints documented
- [ ] Environment variables documented

---

## 🚀 Quick Start Commands

After completing the checklist above, start the platform:

### Development Mode

```bash
# Terminal 1: Redis (optional)
docker run -d -p 6379:6379 --name elson-redis redis:7-alpine

# Terminal 2: Backend
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 3: Frontend
cd frontend
npm start
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Docker Mode

```bash
docker-compose up --build
```

**Access:**
- Backend: http://localhost:8080

### Production Deployment

```bash
# Push to main branch for automatic deployment
git push origin main

# Or deploy manually
gcloud builds submit --config cloudbuild.yaml
```

---

## 🔍 Verification Steps

### 1. Health Check
```bash
curl http://localhost:8000/health
```
Expected: `{"status":"healthy","service":"elson-trading-platform"}`

### 2. Create Test User
- Go to http://localhost:3000
- Click "Register"
- Fill in: email, password, full name
- Submit

### 3. Login
- Use credentials from registration
- Should redirect to dashboard

### 4. Test Market Data
- Navigate to Trading page
- Search for a stock symbol (e.g., AAPL)
- Verify quote data appears

### 5. Test Paper Trading
- Create a portfolio
- Add cash balance
- Place a test order
- Verify order appears in order history

---

## ⚠️ Common Issues

### Backend won't start
```bash
# Check .env file exists and has required values
cat .env

# Verify dependencies installed
pip list | grep fastapi

# Check port not in use
lsof -ti:8000
```

### Frontend won't start
```bash
# Reinstall dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install

# Check for TypeScript errors
npx tsc --noEmit
```

### API calls fail
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check CORS settings in .env
# Ensure frontend URL is in ALLOWED_ORIGINS
```

### Docker build fails
```bash
# Clear Docker cache
docker system prune -a

# Rebuild
docker-compose build --no-cache
docker-compose up
```

---

## 📊 Launch Readiness Score

Calculate your score (total items checked / total items × 100):

- **0-30%**: Not ready - complete environment setup
- **31-60%**: Basic setup complete - install dependencies and configure services
- **61-85%**: Almost ready - complete testing and verification
- **86-95%**: Ready for development launch
- **96-100%**: Production ready 🎉

---

## 🎯 Minimum Requirements for Launch

### Development Launch (Minimum):
1. ✅ `.env` configured with API keys
2. ✅ Dependencies installed (Python + Node)
3. ✅ Backend starts successfully
4. ✅ Frontend starts successfully
5. ✅ Can create account and login

### Production Launch (Recommended):
1. ✅ All development requirements
2. ✅ PostgreSQL database
3. ✅ HTTPS/SSL enabled
4. ✅ Environment variables secured
5. ✅ Monitoring and logging
6. ✅ Automated backups
7. ✅ Tests passing
8. ✅ Security scans clean

---

## 📝 Next Actions

After completing this checklist:

1. **Test thoroughly** with paper trading
2. **Review security settings**
3. **Set up monitoring** (Sentry, CloudWatch, etc.)
4. **Create backups** strategy
5. **Document** any custom configurations
6. **Plan** scaling strategy if needed

---

## ✅ Ready to Launch?

If you've checked all items in sections 1-6, you're ready for development!

If you've checked all items in sections 1-12, you're ready for production!

**Remember:** Always start with paper trading to test strategies before using real money.

---

**Need Help?**
- Review `SETUP_GUIDE.md` for detailed instructions
- Check `README.md` for feature documentation
- Visit http://localhost:8000/docs for API reference
- Create an issue on GitHub for support

Good luck with your launch! 🚀📈
