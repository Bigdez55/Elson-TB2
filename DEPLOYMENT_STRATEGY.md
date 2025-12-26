# Deployment Strategy

## 🧪 Testing/Staging: Vercel
**Purpose**: Quick deployments, PR previews, frontend testing
**Backend**: Lightweight API (no heavy ML)
**Database**: SQLite or Vercel Postgres
**Cost**: Free tier

### Frontend (Vercel)
- **URL**: https://elson-tb-2.vercel.app
- **Auto-deploy**: On merge to main
- **Preview**: Every PR gets preview URL

### Backend (Vercel)
- **URL**: https://elson-tb-2-backend.vercel.app
- **Features**: Core API, lightweight ML (scikit-learn, XGBoost)
- **Limitations**: No TensorFlow/PyTorch (size limits)

---

## 🚀 Production: Google Cloud Platform
**Purpose**: Full production deployment with all features
**Backend**: Complete ML stack (TensorFlow, PyTorch)
**Database**: Cloud SQL PostgreSQL
**Cost**: Pay-as-you-go

### Backend (Cloud Run)
- **Service**: elson-trading-platform
- **Region**: us-central1
- **Features**: Full ML capabilities, auto-scaling
- **Deploy**: `gcloud builds submit --config cloudbuild.yaml`

### Database (Cloud SQL)
- **Type**: PostgreSQL
- **High Availability**: Regional
- **Automated backups**: Daily

---

## 📋 Environment Comparison

| Feature | Vercel (Testing) | GCP (Production) |
|---------|------------------|------------------|
| TensorFlow/PyTorch | ❌ | ✅ |
| Scikit-learn/XGBoost | ✅ | ✅ |
| Auto-scaling | ✅ Limited | ✅ Full |
| Database | SQLite/Vercel | Cloud SQL |
| Cost | Free | ~$200-500/mo |
| Deploy Time | ~2 min | ~5 min |
| ML Model Training | ❌ | ✅ |
| Production Traffic | ❌ | ✅ |

---

## 🔄 Workflow

### Development → Testing → Production

1. **Develop locally**
   ```bash
   cd backend && uvicorn app.main:app --reload
   cd frontend && npm start
   ```

2. **Test on Vercel**
   - Create PR → Auto-deploy to preview URL
   - Merge to main → Deploy to staging
   - Test with real frontend/backend integration

3. **Deploy to GCP Production**
   ```bash
   gcloud builds submit --config cloudbuild.yaml
   ```

---

## ⚙️ Configuration Files

### Current Setup:
- ✅ `vercel.json` - Frontend (root)
- ✅ `backend/vercel.json` - Backend staging
- ✅ `cloudbuild.yaml` - GCP production
- ✅ `backend/requirements.txt` - Lightweight (Vercel)
- ✅ `requirements.txt` - Full ML stack (GCP)

---

## 🎯 Next Steps

**For Testing (Now):**
1. Merge PR to deploy to Vercel
2. Test signup/login/trading features
3. Iterate quickly with PR previews

**For Production (When Ready):**
1. Set up GCP project
2. Configure Cloud SQL database
3. Deploy with full ML stack
4. Point production domain to Cloud Run

---

**Recommendation**: Keep both deployments running so you can test new features on Vercel before pushing to production on GCP.
