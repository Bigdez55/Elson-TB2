# GitHub Secrets Setup for Automated Deployment

This guide shows you how to configure GitHub Secrets so your platform automatically deploys to Google Cloud Run whenever you push to the `main` branch.

## Overview

GitHub Actions will automatically:
1. Run tests
2. Run security scans
3. Build Docker image
4. Deploy to Cloud Run

**All you need to do:** Configure secrets once, then push to `main` branch!

---

## Step 1: Create Google Cloud Service Account

### 1.1 Install gcloud CLI (if not installed)

**macOS:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

**Linux:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

**Windows:**
Download from: https://cloud.google.com/sdk/docs/install

### 1.2 Login and Set Up Project

```bash
# Login to Google Cloud
gcloud auth login

# Set your project (or create new one)
gcloud config set project YOUR_PROJECT_ID

# If creating new project:
gcloud projects create YOUR_PROJECT_ID --name="Elson Trading Platform"
```

### 1.3 Enable Required APIs

```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable iam.googleapis.com
```

### 1.4 Create Service Account

```bash
# Create the service account
gcloud iam service-accounts create elson-deployer \
  --display-name="Elson Trading Platform Deployer" \
  --description="Service account for automated GitHub deployments"

# Get your project ID
PROJECT_ID=$(gcloud config get-value project)

# Grant necessary roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:elson-deployer@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:elson-deployer@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:elson-deployer@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:elson-deployer@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/cloudbuild.builds.builder"
```

### 1.5 Create and Download Service Account Key

```bash
# Create the key file
gcloud iam service-accounts keys create key.json \
  --iam-account=elson-deployer@${PROJECT_ID}.iam.gserviceaccount.com

# The key.json file will be created in your current directory
echo "✅ Service account key created: key.json"
```

**⚠️ IMPORTANT:** Keep this file secure! It provides full access to your Google Cloud project.

---

## Step 2: Configure GitHub Secrets

### 2.1 Go to Your GitHub Repository

1. Navigate to: https://github.com/Bigdez55/Elson-TB2
2. Click **"Settings"** tab
3. In the left sidebar, click **"Secrets and variables"** → **"Actions"**

### 2.2 Add Required Secrets

Click **"New repository secret"** for each of these:

#### Secret 1: GCP_SA_KEY

**Name:** `GCP_SA_KEY`

**Value:** The entire contents of the `key.json` file

```bash
# On macOS/Linux, copy the contents:
cat key.json | pbcopy  # macOS
cat key.json | xclip -selection clipboard  # Linux

# Or just open it and copy manually:
cat key.json
```

Paste the entire JSON content (including the `{ }` brackets).

#### Secret 2: GCP_PROJECT_ID

**Name:** `GCP_PROJECT_ID`

**Value:** Your Google Cloud project ID

```bash
# Get your project ID:
gcloud config get-value project
```

#### Secret 3: SECRET_KEY

**Name:** `SECRET_KEY`

**Value:** `ohrPrvz4l_lXPE5gHIPZAAfmrqbyCHebX9VXpJgjTzA`

(This is the secret key we generated earlier)

#### Secret 4: ALPHA_VANTAGE_API_KEY

**Name:** `ALPHA_VANTAGE_API_KEY`

**Value:** `C9NFHR7SXJZ3T4KE`

#### Secret 5: ALPACA_API_KEY

**Name:** `ALPACA_API_KEY`

**Value:** `PKPMWEVL3HFOCPFGDJCBFE6PPP`

#### Secret 6: ALPACA_SECRET_KEY

**Name:** `ALPACA_SECRET_KEY`

**Value:** `584wKoLe7Nk8Lf2sYzE81w869j9nzkAJ1LGpsJqFVpMC`

### 2.3 Verify Secrets

After adding all secrets, you should see:

```
✅ GCP_SA_KEY
✅ GCP_PROJECT_ID
✅ SECRET_KEY
✅ ALPHA_VANTAGE_API_KEY
✅ ALPACA_API_KEY
✅ ALPACA_SECRET_KEY
```

---

## Step 3: Enable GitHub Actions

### 3.1 Check Workflow File

Your repository already has `.github/workflows/ci.yml` which includes deployment.

### 3.2 Enable Actions (if needed)

1. Go to **"Actions"** tab in your repository
2. If disabled, click **"I understand my workflows, go ahead and enable them"**

---

## Step 4: Update Production Environment Variables

Create a `.env.production` file (for documentation only, **DO NOT commit**):

```env
# Production Environment Variables
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=ohrPrvz4l_lXPE5gHIPZAAfmrqbyCHebX9VXpJgjTzA
DATABASE_URL=sqlite:///./elson_trading.db
ALPHA_VANTAGE_API_KEY=C9NFHR7SXJZ3T4KE
ALPACA_API_KEY=PKPMWEVL3HFOCPFGDJCBFE6PPP
ALPACA_SECRET_KEY=584wKoLe7Nk8Lf2sYzE81w869j9nzkAJ1LGpsJqFVpMC
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ALLOWED_ORIGINS=https://elsontb.com,https://www.elsontb.com
PORT=8080
LOG_LEVEL=INFO
RATE_LIMIT_PER_MINUTE=100
```

These will be set in Cloud Run (done automatically by GitHub Actions).

---

## Step 5: Test Automated Deployment

### 5.1 Create a Pull Request

```bash
# Make a small change (add a comment or update README)
git checkout -b test-deployment
echo "# Test deployment" >> README.md
git add README.md
git commit -m "Test: Trigger automated deployment"
git push origin test-deployment
```

### 5.2 Create PR and Merge

1. Go to GitHub → Pull Requests → Create PR
2. Review the automated checks (tests, security scans)
3. Merge to `main` branch

### 5.3 Watch Deployment

1. Go to **"Actions"** tab
2. Click on the running workflow
3. Watch the deployment progress:
   - ✅ Security scan
   - ✅ Backend tests
   - ✅ Frontend tests
   - ✅ Docker build
   - ✅ Deploy to Cloud Run

### 5.4 Get Deployment URL

After successful deployment, check the logs for the Cloud Run URL:

```
Deployment completed. Service URL: https://elson-trading-platform-xxxxx-uc.a.run.app
```

---

## Step 6: Set Up Custom Domain

Once deployed, map your domain:

```bash
# Map elsontb.com to Cloud Run
gcloud run domain-mappings create \
  --service elson-trading-platform \
  --domain elsontb.com \
  --region us-central1

# Map www.elsontb.com
gcloud run domain-mappings create \
  --service elson-trading-platform \
  --domain www.elsontb.com \
  --region us-central1
```

Then configure DNS (see NAMECHEAP_DNS_SETUP.md).

---

## Troubleshooting

### Error: "Service account does not have permission"

**Solution:** Re-run the IAM binding commands from Step 1.4

### Error: "Invalid key.json format"

**Solution:** Make sure you copied the ENTIRE JSON file, including opening `{` and closing `}`

### Deployment fails with "No API keys found"

**Solution:** Verify all 6 secrets are added in GitHub Settings → Secrets

### Want to update environment variables?

**Option 1:** Update GitHub secrets and re-deploy

**Option 2:** Update directly in Cloud Run:

```bash
gcloud run services update elson-trading-platform \
  --region us-central1 \
  --update-env-vars KEY=VALUE
```

---

## Security Best Practices

✅ **DO:**
- Keep `key.json` secure and never commit it
- Use GitHub Secrets for sensitive data
- Rotate service account keys periodically
- Use separate service accounts for prod/dev

❌ **DON'T:**
- Commit `.env` or `key.json` to git
- Share service account keys
- Use the same keys for development and production
- Grant more permissions than necessary

---

## Clean Up (Optional)

If you need to remove the service account:

```bash
# Delete service account
gcloud iam service-accounts delete elson-deployer@${PROJECT_ID}.iam.gserviceaccount.com

# Delete key file locally
rm key.json
```

---

## Next Steps

After setup:

1. ✅ Push to `main` branch → automatic deployment
2. ✅ Configure custom domain (Namecheap DNS)
3. ✅ Set up monitoring and alerts
4. ✅ Enable Cloud SQL for production database

---

## Quick Reference

### View Deployed Service

```bash
gcloud run services describe elson-trading-platform --region us-central1
```

### View Logs

```bash
gcloud run services logs read elson-trading-platform --region us-central1
```

### Update Service

```bash
gcloud run services update elson-trading-platform \
  --region us-central1 \
  --update-env-vars ENVIRONMENT=production
```

---

**🎉 Once configured, every push to `main` automatically deploys to production!**

No manual deployment needed - just push your code and it's live in minutes!
