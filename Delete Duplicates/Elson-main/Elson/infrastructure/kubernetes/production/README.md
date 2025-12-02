# Elson Wealth App - Production Kubernetes Configuration

This directory contains the Kubernetes manifests for deploying the Elson Wealth App in a production environment.

## Architecture

The production deployment consists of the following components:

- **Backend API**: FastAPI application (3+ replicas)
- **Frontend**: React/Vite application served by Nginx (2+ replicas)
- **Trading Engine**: Python trading execution engine (2+ replicas)
- **PostgreSQL**: Database backend (single instance with backups)
- **Redis**: Cache and message broker (single instance)
- **Nginx Ingress Controller**: For routing external traffic

## Components

### Deployments

- `backend-deployment.yaml`: Backend API service
- `frontend-deployment.yaml`: Frontend web application
- `trading-engine-deployment.yaml`: Trading engine service

### StatefulSets

- `postgres-statefulset.yaml`: PostgreSQL database
- `redis-statefulset.yaml`: Redis cache and message broker

### Services

- `backend-service.yaml`: Backend service (ClusterIP)
- `frontend-service.yaml`: Frontend service (ClusterIP)
- `trading-engine-service.yaml`: Trading engine service (ClusterIP)
- `postgres-service.yaml`: PostgreSQL service (ClusterIP)
- `redis-service.yaml`: Redis service (ClusterIP)

### Ingress

- `ingress.yaml`: Ingress configuration for external access
- `tls-cert.yaml`: TLS certificate configuration

### Config & Storage

- `configmaps.yaml`: Application configuration
- `postgres-pvc.yaml`: Persistent volume claim for PostgreSQL
- `redis-pvc.yaml`: Persistent volume claim for Redis

### Secrets

- `secrets.yaml`: Application secrets
- `aws-secret.yaml`: AWS credentials for backups
- `postgresql-secret.yaml`: PostgreSQL credentials
- `redis-secret.yaml`: Redis credentials

### Security

- `network-policies.yaml`: Network policies for pod communication

### Scaling & Availability

- `hpa.yaml`: Horizontal Pod Autoscalers for dynamic scaling
- `pdb.yaml`: Pod Disruption Budgets for high availability

### Jobs

- `recurring-jobs.yaml`: Scheduled jobs for maintenance tasks

## Deployment

The production environment is deployed using Kustomize. The `kustomization.yaml` file specifies all resources and transformations.

### Prerequisites

- Kubernetes cluster 1.23+
- kubectl 1.23+
- Kustomize 4.5+
- Container registry with the Elson images
- Persistent storage provisioner
- Nginx Ingress Controller
- Cert-Manager for TLS certificates

### Deployment Steps

1. Update the container registry in `kustomization.yaml`
2. Create the required secrets:

```bash
# Create PostgreSQL secret
kubectl create secret generic elson-prod-postgres-secret \
  --from-literal=POSTGRES_USER=your_user \
  --from-literal=POSTGRES_PASSWORD=your_password \
  --namespace=elson-production

# Create Redis secret
kubectl create secret generic elson-prod-redis-secret \
  --from-literal=REDIS_PASSWORD=your_password \
  --namespace=elson-production

# Create backend secrets
kubectl create secret generic elson-prod-backend-secrets \
  --from-literal=DATABASE_URL=postgresql://user:password@postgres-service:5432/elson \
  --from-literal=SECRET_KEY=your_secret_key \
  --from-literal=REDIS_URL=redis://:password@redis-service:6379/0 \
  --namespace=elson-production

# Create AWS secrets
kubectl create secret generic elson-prod-aws-secrets \
  --from-literal=AWS_ACCESS_KEY_ID=your_key_id \
  --from-literal=AWS_SECRET_ACCESS_KEY=your_access_key \
  --namespace=elson-production

# Create API keys
kubectl create secret generic elson-prod-api-keys \
  --from-literal=ALPHA_VANTAGE_API_KEY=your_key \
  --from-literal=FINNHUB_API_KEY=your_key \
  --from-literal=FMP_API_KEY=your_key \
  --from-literal=POLYGON_API_KEY=your_key \
  --from-literal=COINBASE_API_KEY=your_key \
  --from-literal=STRIPE_API_KEY=your_key \
  --from-literal=STRIPE_WEBHOOK_SECRET=your_secret \
  --namespace=elson-production

# Create broker keys
kubectl create secret generic elson-prod-broker-keys \
  --from-literal=SCHWAB_API_KEY=your_key \
  --from-literal=SCHWAB_SECRET=your_secret \
  --namespace=elson-production
```

3. Deploy the application:

```bash
kubectl apply -k .
```

4. Verify the deployment:

```bash
kubectl get all -n elson-production
```

## Monitoring

The production deployment includes Prometheus annotations for monitoring:

- Backend service exposes metrics at `/metrics`
- Trading Engine service exposes metrics at `/metrics`
- Resource requests and limits are configured for all containers

## Scaling

The production deployment includes Horizontal Pod Autoscalers (HPAs) that automatically scale:

- Backend: 3-10 replicas based on CPU and memory utilization
- Frontend: 2-6 replicas based on CPU utilization
- Trading Engine: 2-8 replicas based on CPU and memory utilization

## High Availability

The production deployment includes:

- Pod Disruption Budgets (PDBs) to ensure minimum availability
- Rolling update strategy for deployments
- Readiness and liveness probes for health checking
- Persistent storage for stateful components

## Security

The production deployment includes:

- Network policies to restrict pod communication
- TLS encryption for external traffic
- Secret management for sensitive information
- Non-root container execution
- Resource limits to prevent DoS attacks
- Container security context configuration