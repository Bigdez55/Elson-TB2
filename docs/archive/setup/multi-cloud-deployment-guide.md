# Multi-Cloud Deployment Guide for Elson Wealth Platform

This comprehensive guide provides step-by-step instructions for deploying the Elson Wealth Trading Platform in a multi-cloud environment using AWS as the primary cloud provider and Google Cloud Platform (GCP) as the secondary provider.

## Overview

The Elson Wealth Trading Platform uses a sophisticated multi-cloud architecture to maximize reliability, performance, and specialized capabilities. This guide covers the entire deployment process across both cloud environments.

## Prerequisites

Before beginning deployment, ensure you have:

1. **Access Credentials**:
   - AWS IAM user with administrator access
   - GCP service account with appropriate permissions
   - Terraform Cloud account (optional, for state management)

2. **Tools**:
   - AWS CLI
   - Google Cloud SDK
   - Terraform
   - Docker
   - Git

3. **Domain and DNS**:
   - Registered domain name
   - Access to DNS management

## 1. Infrastructure Setup

### 1.1 Initialize Terraform

```bash
# Clone infrastructure repository
git clone https://github.com/elson-wealth-management/infrastructure.git
cd infrastructure

# Initialize Terraform with multiple providers
terraform init
```

### 1.2 Configure Provider Credentials

Create a `terraform.tfvars` file:

```hcl
# AWS Configuration
aws_region = "us-east-1"
aws_access_key = "YOUR_AWS_ACCESS_KEY"
aws_secret_key = "YOUR_AWS_SECRET_KEY"

# GCP Configuration
gcp_project = "elson-trading-platform"
gcp_region = "us-central1"
gcp_credentials_file = "path/to/service-account-key.json"

# Application Configuration
environment = "production"
domain_name = "elsonwealth.com"
```

### 1.3 Deploy Base Infrastructure

```bash
# Review the Terraform plan
terraform plan -var-file=terraform.tfvars

# Apply the infrastructure changes
terraform apply -var-file=terraform.tfvars
```

This creates the following resources:

**AWS Resources**:
- VPC with public and private subnets
- RDS PostgreSQL database
- ECS cluster and task definitions
- S3 buckets and CloudFront distribution
- IAM roles and policies
- Secrets Manager entries

**GCP Resources**:
- VPC with subnets
- Cloud SQL instance (replica)
- Cloud Run services
- BigQuery datasets
- Identity Platform configuration
- Secret Manager entries

**Cross-Cloud Networking**:
- VPC peering connections
- Cloud Interconnect/VPN setup
- Network security groups

## 2. Database Setup

### 2.1 Primary Database (AWS RDS)

```bash
# Connect to the RDS instance
psql -h ${terraform.output.rds_endpoint} -U admin -d elson_production

# Initialize database schema
cd /workspaces/Elson/Elson/backend
python -m alembic upgrade head
```

### 2.2 Secondary Database (GCP Cloud SQL)

```bash
# Set up database replication
gcloud sql instances patch ${terraform.output.cloudsql_instance_name} \
  --replica-for-external-master \
  --master-host=${terraform.output.rds_endpoint} \
  --master-port=5432 \
  --master-username=replication \
  --master-password=${terraform.output.replication_password}
```

## 3. Secret Management

### 3.1 Configure AWS Secrets

```bash
# Create production secrets
aws secretsmanager create-secret \
  --name elson/production/database \
  --secret-string "{\"username\":\"$DB_USER\",\"password\":\"$DB_PASS\",\"host\":\"$DB_HOST\"}"
```

### 3.2 Configure GCP Secrets

```bash
# Create corresponding GCP secrets
gcloud secrets create elson-prod-database \
  --data-file=/tmp/db_creds.json
```

### 3.3 HashiCorp Vault Integration

For enhanced secret management with HashiCorp Vault:

```bash
# Enable the database secrets engine
vault secrets enable database

# Configure PostgreSQL connection
vault write database/config/elson-db \
  plugin_name=postgresql-database-plugin \
  allowed_roles="backend-role" \
  connection_url="postgresql://{{username}}:{{password}}@${DB_HOST}:5432/elson_production" \
  username="vault" \
  password="$VAULT_DB_PASSWORD"

# Create a role for dynamic credentials
vault write database/roles/backend-role \
  db_name=elson-db \
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
                       GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
  default_ttl="1h" \
  max_ttl="24h"
```

## 4. Backend Deployment

### 4.1 Build and Push Container Images

```bash
# Build AWS container
cd /workspaces/Elson/Elson/backend
docker build -t elson-backend .

# Push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REPO
docker tag elson-backend:latest $ECR_REPO/elson-backend:latest
docker push $ECR_REPO/elson-backend:latest

# Build GCP container for specialized services
docker build -t elson-specialized-service -f Dockerfile.specialized .

# Push to Google Container Registry
gcloud auth configure-docker
docker tag elson-specialized-service gcr.io/$GCP_PROJECT/elson-specialized-service:latest
docker push gcr.io/$GCP_PROJECT/elson-specialized-service:latest
```

### 4.2 Deploy to AWS ECS

```bash
# Deploy ECS service
aws ecs update-service \
  --cluster elson-production \
  --service elson-backend-service \
  --force-new-deployment
```

### 4.3 Deploy to GCP Cloud Run

```bash
# Deploy to Cloud Run
gcloud run deploy elson-specialized-service \
  --image gcr.io/$GCP_PROJECT/elson-specialized-service:latest \
  --platform managed \
  --region us-central1 \
  --set-env-vars="AWS_SECRET_NAME=elson/production/database" \
  --set-secrets="DB_PASSWORD=elson-prod-database:latest"
```

## 5. Frontend Deployment

### 5.1 Build Frontend

```bash
# Build frontend
cd /workspaces/Elson/Elson/frontend
npm ci
npm run build
```

### 5.2 Deploy to AWS S3/CloudFront

```bash
# Deploy to S3
aws s3 sync dist/ s3://elson-frontend-production/ --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id $CLOUDFRONT_DISTRIBUTION_ID \
  --paths "/*"
```

### 5.3 Deploy to Firebase (GCP)

```bash
# Deploy to Firebase
firebase deploy --only hosting
```

## 6. Cross-Cloud Integration

### 6.1 Configure Data Synchronization

```bash
# Set up Cloud Data Fusion pipeline for BigQuery analytics
gcloud data-fusion instances create elson-integration \
  --location=us-central1 \
  --version=6.4.0
```

### 6.2 Set Up Event Bus Integration

```bash
# Create AWS EventBridge rule for cross-cloud events
aws events put-rule \
  --name "CrossCloudEvents" \
  --event-pattern "{\"source\":[\"elson.trading\"]}"

# Create Cloud Function to receive events from AWS
gcloud functions deploy process-aws-events \
  --trigger-http \
  --runtime python39 \
  --entry-point process_event \
  --source ./event-processor
```

## 7. DNS Configuration

```bash
# Configure primary DNS
aws route53 change-resource-record-sets \
  --hosted-zone-id $HOSTED_ZONE_ID \
  --change-batch file://dns-changes.json

# Set up GCP DNS records
gcloud dns record-sets transaction start --zone=elson-zone
gcloud dns record-sets transaction add --zone=elson-zone \
  --name=api-gcp.elsonwealth.com. \
  --type=A \
  --ttl=300 \
  "$(gcloud run services describe elson-specialized-service --platform managed --region us-central1 --format='value(status.url)')"
gcloud dns record-sets transaction execute --zone=elson-zone
```

## 8. WebSocket Configuration for Market Data

### 8.1 AWS WebSocket Services

```bash
# Deploy WebSocket service to ECS
aws ecs update-service \
  --cluster elson-production \
  --service elson-websocket-service \
  --force-new-deployment

# Configure API Gateway for WebSocket proxy
aws apigatewayv2 create-api \
  --name ElsonWebSocketAPI \
  --protocol-type WEBSOCKET \
  --route-selection-expression '$request.body.action'
```

### 8.2 GCP WebSocket Services

```bash
# Deploy fallback WebSocket service to Cloud Run
gcloud run deploy elson-websocket-service \
  --image gcr.io/$GCP_PROJECT/elson-websocket-service:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## 9. Monitoring and Alerting

### 9.1 Set Up CloudWatch Alerts

```bash
# Create CPU utilization alarm
aws cloudwatch put-metric-alarm \
  --alarm-name HighCPUUtilization \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --period 300 \
  --statistic Average \
  --threshold 70 \
  --alarm-actions $SNS_TOPIC_ARN
```

### 9.2 Set Up GCP Monitoring

```bash
# Create Cloud Monitoring alert
gcloud alpha monitoring policies create \
  --policy-from-file=cloud-run-latency-alert.json
```

### 9.3 Configure Cross-Cloud Dashboards

```bash
# Deploy unified monitoring solution
cd monitoring
terraform apply -var-file=production.tfvars
```

## 10. Security Configuration

### 10.1 Enable WAF Protection

```bash
# Configure AWS WAF
aws wafv2 create-web-acl \
  --name ElsonWAF \
  --scope REGIONAL \
  --default-action Block={} \
  --rules file://waf-rules.json \
  --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=ElsonWAF
```

### 10.2 Set Up Cloud Armor (GCP)

```bash
# Configure GCP Cloud Armor
gcloud compute security-policies create elson-security-policy \
  --description "Security policy for Elson application"

gcloud compute security-policies rules create 1000 \
  --security-policy elson-security-policy \
  --description "Block XSS attacks" \
  --expression "evaluatePreconfiguredExpr('xss-stable')" \
  --action "deny-403"
```

### 10.3 Field-Level Encryption for PII

```bash
# Set up KMS keys for field-level encryption
aws kms create-key \
  --description "Elson PII Encryption Key" \
  --key-usage ENCRYPT_DECRYPT

# Configure GCP Cloud KMS
gcloud kms keyrings create elson-keys \
  --location global

gcloud kms keys create pii-encryption-key \
  --keyring elson-keys \
  --location global \
  --purpose encryption
```

## 11. Redis Deployment

### 11.1 AWS ElastiCache with Redis Sentinel

```bash
# Create Redis Sentinel cluster
aws elasticache create-replication-group \
  --replication-group-id elson-redis-prod \
  --replication-group-description "Redis for Elson production" \
  --engine redis \
  --engine-version 6.2 \
  --num-cache-clusters 3 \
  --cache-node-type cache.m5.large \
  --automatic-failover-enabled \
  --subnet-group-name elson-redis-subnet-group
```

### 11.2 GCP Memorystore for Redis

```bash
# Create Redis instance
gcloud redis instances create elson-redis-gcp \
  --region=us-central1 \
  --tier=standard \
  --size=5 \
  --redis-version=redis_6_x
```

## 12. Production Verification

### 12.1 Run System Health Checks

```bash
# Verify AWS services
./scripts/verify_aws_deployment.sh

# Verify GCP services
./scripts/verify_gcp_deployment.sh

# Verify cross-cloud integrations
./scripts/verify_cross_cloud_integration.sh
```

### 12.2 Load Testing

```bash
# Run load tests against production environment
cd load-tests
npm run test:production
```

### 12.3 Verify Database Replication

```bash
# Test database replication
./scripts/verify_database_replication.sh
```

## 13. Circuit Breaker Verification

```bash
# Test AWS circuit breaker
curl https://api.elsonwealth.com/api/v1/health/circuit-breaker-status

# Test GCP circuit breaker
curl https://api-gcp.elsonwealth.com/api/v1/health/circuit-breaker-status
```

## 14. Post-Deployment Tasks

### 14.1 Backup Verification

```bash
# Test database backup and restore
./scripts/test_rds_backup_restore.sh
```

### 14.2 Disaster Recovery Test

```bash
# Test failover to GCP
./scripts/test_aws_to_gcp_failover.sh
```

### 14.3 Security Scan

```bash
# Run comprehensive security scan
./scripts/security_scan.sh
```

## 15. Documentation

Ensure the following documentation is updated:

1. Architecture diagrams
2. Runbooks for common operational tasks
3. Emergency procedures
4. Contact information for support

### 15.1 Update Operations Manual

```bash
# Generate updated documentation
cd /workspaces/Elson/docs
./generate_ops_manual.sh
```

## Troubleshooting

### Common Issues

1. **Cross-Cloud Connectivity**:
   - Check VPC peering status
   - Verify security group/firewall rules
   - Test network connectivity

2. **Database Replication**:
   - Verify replication status
   - Check for replication lag
   - Validate data consistency

3. **Authentication Issues**:
   - Check IAM/service account permissions
   - Verify secret access

### Support Contacts

For deployment issues, contact:

- Primary Cloud (AWS): cloud-ops@elsonwealth.com
- Secondary Cloud (GCP): gcp-support@elsonwealth.com
- Cross-Cloud Integration: multi-cloud@elsonwealth.com

## Additional Resources

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/index.html)
- [GCP Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Terraform Multi-Cloud Patterns](https://www.terraform.io/docs/cloud/guides/recommended-patterns/multi-cloud-patterns.html)
- [Cloud Interconnect Documentation](https://cloud.google.com/network-connectivity/docs/interconnect)
- [Multi-Cloud Architecture Documentation](../architecture/multi-cloud-architecture.md)