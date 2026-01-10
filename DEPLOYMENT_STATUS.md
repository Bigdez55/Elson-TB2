# Elson-TB2 Deployment Status

**Last Updated:** 2026-01-10
**Region:** us-west1 (all services)
**Project:** elson-33a95

---

## Current Status

### Frontend: WORKING
- **URL:** https://elson-frontend-490677787763.us-west1.run.app (or similar)
- **API URL baked in:** `https://elson-backend-490677787763.us-west1.run.app/api/v1`
- **Build:** Successful (with `--legacy-peer-deps` flag)

### Backend: NOT DEPLOYED
- **Expected URL:** https://elson-backend-490677787763.us-west1.run.app
- **Current Cloud Run services in us-west1:**
  - `idx-elson-tb2git-26326678` (old, from Jan 3) - https://idx-elson-tb2git-26326678-490677787763.us-west1.run.app
- **Status:** `elson-backend` service does not exist yet - needs to be deployed
- **Cloud SQL:** Should connect via us-west1

---

## Issues Found

### 1. package-lock.json Issue
- The `package-lock.json` in frontend had dependency conflicts
- **Fix:** Use `npm install --legacy-peer-deps` when installing

### 2. Global vs Regional Builds
- Builds were running in `global` region instead of `us-west1`
- Global builds fail because they can't connect to Cloud SQL in us-west1
- **Fix:** Always specify `--region us-west1` in deploy commands

### 3. Cancelled Builds
- Build `ca00e447-f7f2-4a12-b719-816daef426ab` was cancelled (was stuck for 17+ minutes)
- No Cloud Build triggers are configured (builds are manual)

---

## Next Steps

1. [ ] Fix backend deployment to us-west1
2. [ ] Verify Cloud SQL connection string is correct
3. [ ] Ensure backend Dockerfile/cloudbuild.yaml uses correct region
4. [ ] Test backend health endpoint
5. [ ] Verify frontend can communicate with backend

---

## Deployment Commands

### Frontend Build (local)
```bash
cd /home/bigdez55/Elson-TB2/frontend
npm install --legacy-peer-deps
REACT_APP_API_URL=https://elson-backend-490677787763.us-west1.run.app/api/v1 npm run build
```

### Deploy to Cloud Run (always use us-west1)
```bash
# Backend
cd /home/bigdez55/Elson-TB2/backend
gcloud run deploy elson-backend \
  --source . \
  --region us-west1 \
  --platform managed

# Frontend
cd /home/bigdez55/Elson-TB2/frontend
gcloud run deploy elson-frontend \
  --source . \
  --region us-west1 \
  --platform managed
```

### Cancel stuck global builds
```bash
gcloud builds list --limit=5
gcloud builds cancel BUILD_ID
```

---

## GCP Resources

| Resource | Region | Status |
|----------|--------|--------|
| Cloud SQL | us-west1 | Active |
| Cloud Run (backend) | us-west1 | Needs fix |
| Cloud Run (frontend) | us-west1 | Working |
| Cloud Build triggers | N/A | None configured |

---

## Troubleshooting Notes

- If builds hang, check if they're running in `global` - cancel and redeploy with `--region us-west1`
- Frontend needs `--legacy-peer-deps` due to dependency conflicts
- Backend must have Cloud SQL connection string for us-west1 instance
