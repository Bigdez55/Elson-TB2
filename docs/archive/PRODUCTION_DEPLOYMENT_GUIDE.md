# Production Deployment Guide for Elson Wealth Platform

This guide provides step-by-step instructions for deploying the Elson Wealth Platform to production.

## Prerequisites

Before beginning production deployment, ensure you have:

1. **Production-ready infrastructure** (Kubernetes cluster, PostgreSQL, Redis)
2. **Valid API keys** from all required providers
3. **SSL certificates** for HTTPS communication
4. **Monitoring and alerting** systems in place
5. **Backup and disaster recovery** procedures

## Step 1: Environment Configuration

### 1.1 Create Production Environment File

Copy the production environment template:
```bash
cp Elson/config/production.env.example Elson/config/production.env
```

### 1.2 Configure Required Environment Variables

**Database Configuration:**
```env
DATABASE_URL=postgresql://elson_user:secure_password@elson-db:5432/elson_production
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
```

**Redis Configuration:**
```env
REDIS_URL=redis://:redis_password@elson-redis:6379/0
REDIS_PASSWORD=secure_redis_password
REDIS_SENTINEL_ENABLED=true
REDIS_SENTINEL_HOSTS=sentinel-1:26379,sentinel-2:26379,sentinel-3:26379
```

**Security Configuration:**
```env
SECRET_KEY=your_64_character_random_secret_key_here
DEBUG=false
ENVIRONMENT=production
ALLOWED_ORIGINS='["https://app.elsonwealth.com"]'
```

**API Keys (obtain production keys from providers):**
```env
ALPHA_VANTAGE_API_KEY=your_production_alpha_vantage_key
FINNHUB_API_KEY=your_production_finnhub_key
FMP_API_KEY=your_production_fmp_key
POLYGON_API_KEY=your_production_polygon_key
SCHWAB_API_KEY=your_production_schwab_key
SCHWAB_SECRET=your_production_schwab_secret
ALPACA_API_KEY_ID=your_production_alpaca_key
ALPACA_API_SECRET=your_production_alpaca_secret
```

**Payment Processing:**
```env
STRIPE_API_KEY=sk_live_your_stripe_live_key
STRIPE_WEBHOOK_SECRET=whsec_your_stripe_webhook_secret
```

## Step 2: Obtain Production API Keys

### 2.1 Market Data Providers

1. **Alpha Vantage**
   - Visit: https://www.alphavantage.co/support/#api-key
   - Upgrade to premium plan for production limits
   - Replace test key in environment file

2. **Finnhub**
   - Visit: https://finnhub.io/register
   - Subscribe to appropriate plan for your volume
   - Generate production API key

3. **Financial Modeling Prep**
   - Visit: https://financialmodelingprep.com/developer/docs
   - Subscribe to professional plan
   - Generate production API key

4. **Polygon.io**
   - Visit: https://polygon.io/
   - Subscribe to appropriate tier
   - Generate production API key

### 2.2 Broker APIs

1. **Charles Schwab**
   - Apply for production API access
   - Complete certification process
   - Obtain production credentials

2. **Alpaca**
   - Visit: https://alpaca.markets/
   - Complete KYC process
   - Generate live trading keys

## Step 3: Pre-Deployment Validation

### 3.1 Run Production Readiness Check

```bash
cd Elson/backend
python -m app.scripts.check_production_readiness \
  --env-file ../config/production.env \
  --output production_check_results.json \
  --verbose
```

### 3.2 Validate All Checks Pass

Ensure all critical checks pass:
- ✅ Environment variables configured
- ✅ Database connection successful
- ✅ Redis connection successful
- ✅ All API integrations working
- ✅ No test/development keys in use

## Step 4: Database Setup

### 4.1 Initialize Production Database

```bash
# Run database migrations
cd Elson/backend
export ENV_FILE=../config/production.env
python -m alembic upgrade head
```

### 4.2 Create Initial Superuser

```bash
python -m app.scripts.create_superuser \
  --email admin@elsonwealth.com \
  --username admin \
  --password secure_admin_password
```

## Step 5: Kubernetes Deployment

### 5.1 Update Kubernetes Configurations

```bash
cd Elson/infrastructure/kubernetes/production
```

Update the following files with your production values:
- `secrets.yaml` - Add your environment variables as secrets
- `configmaps.yaml` - Add non-sensitive configuration
- `ingress.yaml` - Configure your domain and SSL certificates

### 5.2 Deploy Infrastructure Components

```bash
# Deploy in order
kubectl apply -f postgres-statefulset.yaml
kubectl apply -f redis-statefulset.yaml
kubectl apply -f secrets.yaml
kubectl apply -f configmaps.yaml
```

### 5.3 Deploy Application Components

```bash
kubectl apply -f backend-deployment.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f websocket-deployment.yaml
kubectl apply -f trading-engine-deployment.yaml
```

### 5.4 Deploy Services and Ingress

```bash
kubectl apply -f backend-service.yaml
kubectl apply -f frontend-service.yaml
kubectl apply -f websocket-service.yaml
kubectl apply -f ingress.yaml
```

## Step 6: Post-Deployment Verification

### 6.1 Health Checks

```bash
# Check API health
curl https://api.elsonwealth.com/health

# Check WebSocket connectivity
wscat -c wss://api.elsonwealth.com/ws

# Check database connectivity
kubectl exec -it postgres-0 -- psql -U elson_user -d elson_production -c "SELECT 1;"
```

### 6.2 Verify Critical Services

1. **Market Data Streaming**
   ```bash
   # Check market data is flowing
   curl https://api.elsonwealth.com/api/v1/market/quote/AAPL
   ```

2. **Trading Functionality**
   ```bash
   # Verify paper trading works
   curl -X POST https://api.elsonwealth.com/api/v1/trading/paper-trade \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"symbol": "AAPL", "side": "buy", "quantity": 1}'
   ```

3. **User Authentication**
   ```bash
   curl -X POST https://api.elsonwealth.com/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "secure_admin_password"}'
   ```

## Step 7: Monitoring and Alerting

### 7.1 Configure Prometheus Monitoring

```bash
kubectl apply -f prometheus-alertmanager.yaml
```

### 7.2 Set Up Grafana Dashboards

```bash
kubectl apply -f grafana-dashboards-configmap.yaml
```

### 7.3 Configure Alerting Rules

Key alerts to configure:
- High error rates (>5%)
- Database connection failures
- Redis connection failures
- High response times (>2s)
- Failed broker operations
- Memory/CPU usage above 80%

## Step 8: Security Hardening

### 8.1 Network Policies

```bash
kubectl apply -f network-policies.yaml
```

### 8.2 Pod Security Policies

Ensure all pods run with:
- Non-root user
- Read-only root filesystem where possible
- Resource limits configured
- Security contexts applied

### 8.3 Secret Management

- Use Kubernetes secrets for sensitive data
- Enable secret encryption at rest
- Rotate secrets regularly
- Use HashiCorp Vault for advanced secret management

## Step 9: Backup and Disaster Recovery

### 9.1 Database Backups

```bash
# Set up automated daily backups
kubectl apply -f postgres-backup-cronjob.yaml
```

### 9.2 Configuration Backups

- Backup Kubernetes configurations
- Backup environment configurations
- Document recovery procedures

## Troubleshooting

### Common Issues

1. **API Key Validation Failures**
   - Verify keys are production keys, not test keys
   - Check API quotas and limits
   - Verify key permissions

2. **Database Connection Issues**
   - Check connection string format
   - Verify database user permissions
   - Check network connectivity

3. **Redis Connection Failures**
   - Verify Redis authentication
   - Check Sentinel configuration
   - Validate network policies

4. **Broker Integration Failures**
   - Verify broker credentials
   - Check broker-specific configuration
   - Validate paper trading vs live trading settings

### Getting Help

- Check application logs: `kubectl logs -f deployment/elson-backend`
- Check system metrics in Grafana
- Review production readiness check results
- Contact support with specific error messages

## Maintenance

### Regular Maintenance Tasks

1. **Weekly:**
   - Review monitoring dashboards
   - Check backup status
   - Review security logs

2. **Monthly:**
   - Update dependencies
   - Rotate secrets
   - Review performance metrics

3. **Quarterly:**
   - Security audit
   - Disaster recovery testing
   - Performance optimization review

## Security Considerations

1. **API Security:**
   - Rate limiting enabled
   - CSRF protection active
   - JWT tokens with expiration
   - 2FA for admin accounts

2. **Data Protection:**
   - PII encryption enabled
   - Database encryption at rest
   - TLS for all communications
   - Regular security scans

3. **Access Control:**
   - Role-based permissions
   - Audit logging enabled
   - Principle of least privilege
   - Regular access reviews

---

For additional support or questions about production deployment, please refer to the main documentation or contact the development team.