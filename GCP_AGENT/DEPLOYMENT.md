# Elson Trading Platform - Deployment Guide

## Quick Reference

**Backend URL:** `https://elson-backend-490677787763.us-west1.run.app`
**Region:** `us-west1`
**Project:** `elson-33a95`

## Files That Matter for Deployment

### Backend
| File | Purpose |
|------|---------|
| `Dockerfile` | Backend container build (root directory) |
| `requirements-docker.txt` | **Python dependencies for production Docker builds** |
| `cloudbuild.yaml` | Cloud Build configuration for both frontend & backend |

### Frontend
| File | Purpose |
|------|---------|
| `frontend/Dockerfile` | Frontend container build |
| `frontend/package.json` | Node.js dependencies |
| `frontend/package-lock.json` | Locked dependency versions (required for npm ci) |

### NOT Used for Cloud Run Deployment
| File | Note |
|------|------|
| `backend/requirements.txt` | Only for local development, NOT used by Dockerfile |
| `requirements-production.txt` | Legacy file, NOT used |

## How to Deploy

### Full Deployment (Backend + Frontend)
```bash
cd /home/bigdez55/Elson-TB2
COMMIT_SHA=$(git rev-parse --short HEAD)
gcloud builds submit --config=cloudbuild.yaml --substitutions=COMMIT_SHA=$COMMIT_SHA --timeout=1200s
```

### Backend Only
```bash
gcloud run deploy elson-backend \
  --image=gcr.io/elson-33a95/elson-backend:TAG \
  --region=us-west1 \
  --platform=managed \
  --allow-unauthenticated \
  --port=8080 \
  --memory=1Gi \
  --cpu=1 \
  --max-instances=10 \
  --min-instances=1 \
  --add-cloudsql-instances=elson-33a95:us-west1:elson-postgres \
  --set-env-vars=ENVIRONMENT=production,PROJECT_ID=elson-33a95,CLOUD_SQL_CONNECTION_NAME=elson-33a95:us-west1:elson-postgres,DB_USER=postgres,DB_NAME=elson_trading,DATABASE_URL='postgresql://postgres@/elson_trading?host=/cloudsql/elson-33a95:us-west1:elson-postgres' \
  --update-secrets=DB_PASS=DB_PASSWORD:latest,SECRET_KEY=SECRET_KEY:latest \
  --quiet
```

## Known Issues and Fixes

### 1. bcrypt/passlib Compatibility
**Problem:** Login fails with `AttributeError: module 'bcrypt' has no attribute '__about__'`

**Cause:** bcrypt 4.x has breaking changes with passlib 1.7.4

**Fix:** Use `bcrypt==3.2.2` in `requirements-docker.txt`:
```
passlib[bcrypt]>=1.7.4
bcrypt==3.2.2  # Last version with full passlib compatibility (4.x breaks passlib)
```

### 2. Frontend npm ci Fails
**Problem:** `npm ci` fails with ERESOLVE peer dependency error

**Cause:** react-scripts@5.0.1 requires TypeScript 4.x but project uses TypeScript 5.x

**Fix:** Use `--legacy-peer-deps` in `frontend/Dockerfile`:
```dockerfile
RUN npm ci --legacy-peer-deps
```

### 3. Cloud Build COMMIT_SHA Error
**Problem:** `invalid image name "gcr.io/PROJECT/image:"` when running cloudbuild.yaml

**Cause:** COMMIT_SHA variable not set when running manually

**Fix:** Always provide COMMIT_SHA substitution:
```bash
COMMIT_SHA=$(git rev-parse --short HEAD)
gcloud builds submit --config=cloudbuild.yaml --substitutions=COMMIT_SHA=$COMMIT_SHA
```

### 4. Cloud Run Forbidden Error
**Problem:** 403 Forbidden when accessing Cloud Run service

**Cause:** IAM policy doesn't allow unauthenticated access

**Fix:**
```bash
gcloud run services add-iam-policy-binding elson-backend \
  --member="allUsers" \
  --role="roles/run.invoker" \
  --region=us-west1
```

## Verification Commands

### Check Backend Health
```bash
curl https://elson-backend-490677787763.us-west1.run.app/health
```

### Check Recent Logs
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=elson-backend AND resource.labels.location=us-west1" --limit=20
```

### List Available Images
```bash
gcloud container images list-tags gcr.io/elson-33a95/elson-backend --limit=5
gcloud container images list-tags gcr.io/elson-33a95/elson-frontend --limit=5
```

## Cloud SQL Configuration

- **Instance:** `elson-postgres`
- **Region:** `us-west1` (NOT a zone like us-west1-a)
- **Database:** `elson_trading`
- **User:** `postgres`
- **Connection:** Via Cloud SQL proxy built into Cloud Run

### Required Secrets (Secret Manager)
- `DB_PASSWORD` - Database password
- `SECRET_KEY` - JWT signing key

## Deployment Checklist

Before deploying:
1. [ ] Ensure `requirements-docker.txt` has correct versions (bcrypt==3.2.2)
2. [ ] Ensure `frontend/Dockerfile` uses `--legacy-peer-deps`
3. [ ] Commit and push all changes to git
4. [ ] Provide COMMIT_SHA when using cloudbuild.yaml manually

After deploying:
1. [ ] Check `/health` endpoint returns `{"status":"healthy"}`
2. [ ] Check database connection shows `"connected": true`
3. [ ] Test login functionality
4. [ ] Check logs for errors

## File Cleanup Recommendations

Consider removing these files to reduce confusion:
- `requirements-production.txt` - Duplicate of requirements-docker.txt
- Keep only `requirements-docker.txt` for production

---
Last Updated: 2026-01-21
