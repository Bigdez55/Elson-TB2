# Elson Wealth Platform - Production Deployment Guide

## Overview

The Elson Wealth Platform uses **Google Cloud Platform (GCP) as a single cloud provider** for optimal cost efficiency, simplified architecture, and superior Kubernetes/container capabilities.

## Architecture

- **Frontend**: React SPA deployed to GCP Cloud Run
- **Backend**: FastAPI application deployed to GCP Cloud Run  
- **Trading Engine**: Python microservice deployed to GCP Cloud Run
- **Database**: Cloud SQL PostgreSQL with private IP
- **Cache**: Memory Store Redis
- **Container Registry**: Artifact Registry
- **Secrets**: Secret Manager
- **Authentication**: Workload Identity Federation

## Cost Benefits of Single Provider (GCP)

### Financial Advantages
- **25-50% cheaper** than AWS for equivalent services
- **Automatic sustained use discounts** (no upfront commitments)
- **Predictable pricing**: GCP changes prices 0.35x/month vs AWS 197x/month
- **Simplified billing**: Single vendor, unified costs

### Technical Advantages  
- **Kubernetes Excellence**: GCP created Kubernetes, superior GKE experience
- **Network Efficiency**: All services in same VPC, lower latency, reduced egress costs
- **Simplified Operations**: One vendor, one support system, unified monitoring
- **Better Integration**: Seamless service-to-service communication

### Estimated Monthly Costs
- **Cloud Run (3 services)**: $200-500
- **Cloud SQL (PostgreSQL)**: $150-300  
- **Memory Store Redis**: $100-200
- **Artifact Registry**: $10-20
- **Load Balancer**: $20-50
- **Secret Manager**: $5-10
- **Total**: $485-1,080/month

## Prerequisites

### 1. GCP Project Setup

Run the automated infrastructure setup:
```bash
# Set your project ID
export GCP_PROJECT_ID="your-project-id"

# Run infrastructure setup script
./scripts/setup-gcp-infrastructure.sh
```

This script creates:
- Enables required APIs
- Artifact Registry repository
- Cloud SQL PostgreSQL instance
- Memory Store Redis instance
- VPC network and subnet
- VPC connector for Cloud Run
- Service accounts with proper permissions
- Sample secrets in Secret Manager

### 2. Workload Identity Federation

Set up secure GitHub Actions authentication:

```bash
# Create workload identity pool
gcloud iam workload-identity-pools create github-pool \
  --location=global \
  --description="GitHub Actions Pool"

# Create OIDC provider
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location=global \
  --workload-identity-pool=github-pool \
  --issuer-uri=https://token.actions.githubusercontent.com \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository == 'YOUR_GITHUB_USERNAME/YOUR_REPO_NAME'"

# Bind service account
gcloud iam service-accounts add-iam-policy-binding \
  github-actions@$PROJECT_ID.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME"
```

### 3. GitHub Secrets Configuration

Configure all required secrets listed in `GITHUB_SECRETS_SETUP.md`:

**Required Core Secrets:**
```bash
GCP_PROJECT_ID=your-project-id
WIF_PROVIDER=projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider
WIF_SERVICE_ACCOUNT=github-actions@your-project.iam.gserviceaccount.com
CLOUD_RUN_SERVICE_ACCOUNT=cloud-run-sa@your-project.iam.gserviceaccount.com
DATABASE_URL=postgresql://user:pass@/db?host=/cloudsql/project:region:instance
REDIS_URL=redis://PRIVATE_IP:6379
# ... plus all API keys and external service credentials
```

## Deployment Workflows

### Unified GCP Deployment

The platform uses a single workflow (`deploy-backend-gcp.yml`) that deploys both frontend and backend to Cloud Run:

```bash
# Deploy to staging (automatic on main branch push)
git push origin main

# Deploy to production (manual)
gh workflow run "Deploy to GCP (Backend + Frontend)" -f environment=production -f deploy_trading_engine=true
```

### Deployment Process

The workflow automatically:
1. **Tests**: Frontend (TypeScript, lint, build) + Backend (Python tests) + Trading Engine
2. **Builds**: Docker images for all services
3. **Deploys**: All services to Cloud Run with proper configuration
4. **Migrates**: Database schema changes
5. **Validates**: Health checks and smoke tests
6. **Notifies**: Deployment status

### Environment Configuration

**Staging Environment:**
- Automatic deployment on `main` branch push
- Uses staging secrets and configuration
- Lower resource limits
- Paper trading enabled

**Production Environment:**
- Manual deployment only
- Production secrets and configuration
- Higher resource limits and scaling
- Real trading (paper trading disabled)

## Security Features

### Secrets Management
- **GCP Secret Manager**: All sensitive data stored securely
- **Workload Identity Federation**: No service account keys
- **Environment-based secrets**: Separate staging/production values
- **Automatic rotation**: Supported for all external API keys

### Network Security
- **Private VPC**: All services communicate privately  
- **Cloud SQL private IP**: No public database access
- **Memory Store private**: Redis only accessible via VPC
- **Cloud Run private**: Services communicate through VPC connector

### Application Security
- **TLS termination**: Automatic HTTPS for all services
- **Security headers**: CSP, HSTS, XSS protection
- **Container security**: Non-root users, minimal base images
- **Secret injection**: Runtime secret access via Secret Manager

## Monitoring & Observability

### Health Checks
- **Frontend**: `https://frontend-env.a.run.app/health`
- **Backend**: `https://backend-env.a.run.app/health`  
- **Trading Engine**: `https://trading-engine-env.a.run.app/health`

### Logging
- **Cloud Logging**: Centralized log aggregation
- **Structured logging**: JSON format for parsing
- **Log retention**: 90 days default
- **Real-time monitoring**: Error alerting

### Metrics
- **Cloud Monitoring**: Built-in metrics and alerting
- **Custom metrics**: Application-specific monitoring
- **SLA tracking**: Uptime and performance monitoring
- **Cost monitoring**: Resource usage and billing alerts

## Scaling & Performance

### Auto-scaling Configuration
- **Frontend**: 0-10 instances, 1 CPU, 512Mi memory
- **Backend**: 0-100 instances, 2 CPU, 2Gi memory  
- **Trading Engine**: 1-50 instances, 1 CPU, 1Gi memory

### Performance Optimizations
- **Connection pooling**: Database and Redis
- **Caching**: Redis for frequent data
- **CDN**: Cloud Run global load balancing
- **Compression**: Gzip enabled for all text content

## Disaster Recovery

### Backup Strategy
- **Database**: Automated daily backups with 7-day retention
- **Point-in-time recovery**: Available for critical incidents
- **Configuration backup**: Infrastructure as code in git
- **Secret backup**: Manual backup procedure for critical secrets

### Rollback Procedures

**Frontend/Backend Rollback:**
```bash
# List revisions
gcloud run revisions list --service=backend-production

# Route traffic to previous revision
gcloud run services update-traffic backend-production \
  --to-revisions=backend-production-00001-abc=100
```

**Database Rollback:**
```bash
# Create clone from backup
gcloud sql instances clone elson-db elson-db-restore \
  --point-in-time=2024-01-01T10:00:00Z
```

## Troubleshooting

### Common Issues

1. **Deployment Failures**
   - Check GitHub Actions logs
   - Verify all secrets are configured
   - Ensure service account permissions

2. **Database Connection Issues**  
   - Verify Cloud SQL private IP connectivity
   - Check VPC connector configuration
   - Validate connection string format

3. **Secret Access Issues**
   - Confirm Secret Manager permissions
   - Verify secret names match workflow
   - Check service account bindings

### Support Contacts
- **Infrastructure Issues**: Review GCP Console logs
- **Application Issues**: Check Cloud Run logs  
- **Database Issues**: Monitor Cloud SQL metrics
- **Security Issues**: Review Secret Manager audit logs

## Migration from Multi-Cloud

If migrating from AWS frontend + GCP backend:

1. **Data Migration**: Export S3 static assets (handled by build process)
2. **DNS Updates**: Point domain to Cloud Run frontend URL
3. **SSL Certificates**: Automatic via Cloud Run managed certificates
4. **CDN**: Cloud Run provides global load balancing
5. **Monitoring**: Migrate alerts to Cloud Monitoring

## Cost Optimization Tips

1. **Right-sizing**: Monitor and adjust CPU/memory limits
2. **Scaling**: Set appropriate min/max instances
3. **Regional deployment**: Use single region to reduce costs
4. **Committed use**: Apply discounts for stable workloads
5. **Monitoring**: Set up billing alerts and budgets

The single-provider GCP architecture provides significant cost savings, operational simplicity, and technical advantages while maintaining enterprise-grade security and reliability.