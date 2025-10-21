# Elson Trading Platform - Quick Start Guide

Get your platform deployed to **Elsontb.com** in 3 simple steps!

---

## 🎯 Goal

Deploy your platform to Google Cloud Run and make it accessible at **https://elsontb.com**

---

## ⚡ Quick Start (Choose Your Path)

### Path A: Automatic Deployment via GitHub (Easiest)

**Best for:** Continuous deployment, automatic updates

**Time:** 30 minutes

1. **Configure GitHub Secrets** (one-time setup)
   - Follow: `GITHUB_SECRETS_SETUP.md`
   - Add 6 secrets to GitHub repository

2. **Push to Main Branch**
   ```bash
   git push origin main
   ```

3. **Configure DNS at Namecheap**
   - Follow: `NAMECHEAP_DNS_SETUP.md`
   - Add DNS records

**Done!** Every push to `main` auto-deploys to production.

---

### Path B: Manual Deployment Script (Quick)

**Best for:** One-time deployment, more control

**Time:** 15 minutes

1. **Install gcloud CLI** (if not installed)
   ```bash
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   gcloud init
   ```

2. **Run Deployment Script**
   ```bash
   cd /home/user/Elson-TB2
   ./deploy-to-cloud-run.sh
   ```

3. **Configure DNS at Namecheap**
   - Follow: `NAMECHEAP_DNS_SETUP.md`

**Done!** Your app is live!

---

### Path C: Local Development First

**Best for:** Testing before deployment

**Time:** 5 minutes

1. **Start Backend**
   ```bash
   cd /home/user/Elson-TB2/backend
   python -m uvicorn app.main:app --reload --port 8000
   ```

2. **Start Frontend** (separate terminal)
   ```bash
   cd /home/user/Elson-TB2/frontend
   npm start
   ```

3. **Test Locally**
   - Frontend: http://localhost:3000
   - API: http://localhost:8000/docs

4. **Deploy** when ready (use Path A or B)

---

## 📚 Detailed Guides

All guides are in your repository:

| Guide | Purpose | Time |
|-------|---------|------|
| `GITHUB_SECRETS_SETUP.md` | Configure automated deployment | 30 min |
| `NAMECHEAP_DNS_SETUP.md` | Point domain to Cloud Run | 15 min |
| `DEPLOYMENT_GUIDE.md` | Complete deployment options | Reference |
| `SETUP_GUIDE.md` | Detailed local setup | Reference |
| `LAUNCH_CHECKLIST.md` | Pre-launch checklist | Reference |

---

## ✅ What's Already Done

You're ahead of the game! Already completed:

- ✅ All configuration files created
- ✅ `.env` configured with API keys
- ✅ Dependencies installed (backend + frontend)
- ✅ Tested and working locally
- ✅ Docker configuration ready
- ✅ CI/CD pipeline configured
- ✅ Domain configured (elsontb.com)

---

## 🚀 Recommended: Automated Deployment

**Best approach for production:**

### Step 1: GitHub Secrets (One-Time, 30 min)

```bash
# 1. Create Google Cloud service account
gcloud iam service-accounts create elson-deployer \
  --display-name="Elson Trading Deployer"

# 2. Grant permissions (see GITHUB_SECRETS_SETUP.md for full commands)

# 3. Create key
gcloud iam service-accounts keys create key.json \
  --iam-account=elson-deployer@PROJECT_ID.iam.gserviceaccount.com

# 4. Add to GitHub Secrets:
#    - GCP_SA_KEY (contents of key.json)
#    - GCP_PROJECT_ID
#    - SECRET_KEY
#    - ALPHA_VANTAGE_API_KEY
#    - ALPACA_API_KEY
#    - ALPACA_SECRET_KEY
```

### Step 2: Deploy (2 min)

```bash
git push origin main
```

That's it! GitHub Actions handles:
- ✅ Running tests
- ✅ Security scans
- ✅ Building Docker image
- ✅ Deploying to Cloud Run

### Step 3: DNS Configuration (15 min + propagation time)

Follow `NAMECHEAP_DNS_SETUP.md`:

1. Login to Namecheap
2. Go to Elsontb.com → Advanced DNS
3. Add Google Cloud Run A records
4. Add CNAME for www subdomain
5. Wait for DNS propagation (2-24 hours)

**Result:** https://elsontb.com is live! 🎉

---

## 🔧 Configuration Summary

Your current configuration:

### Environment Variables
```env
✅ SECRET_KEY=ohrPrvz4l_lXPE5gHIPZAAfmrqbyCHebX9VXpJgjTzA
✅ ALPHA_VANTAGE_API_KEY=C9NFHR7SXJZ3T4KE
✅ ALPACA_API_KEY=PKPMWEVL3HFOCPFGDJCBFE6PPP
✅ ALPACA_SECRET_KEY=584wKoLe7Nk8Lf2sYzE81w869j9nzkAJ1LGpsJqFVpMC
✅ ALPACA_BASE_URL=https://paper-api.alpaca.markets (Paper Trading)
✅ ALLOWED_ORIGINS=...elsontb.com...
```

### Services Configured
- ✅ Alpha Vantage (Market Data)
- ✅ Alpaca (Paper Trading)
- ✅ MCP Server (Claude integration)

---

## 💡 Pro Tips

### 1. Test Locally First
Always test changes locally before deploying:
```bash
cd backend && python -m uvicorn app.main:app --reload --port 8000
cd frontend && npm start
```

### 2. Use Paper Trading
Your Alpaca account is set to paper trading (no real money). Test strategies first!

### 3. Monitor Your Deployment
```bash
# View logs
gcloud run services logs read elson-trading-platform --region us-central1

# Check status
gcloud run services describe elson-trading-platform --region us-central1
```

### 4. DNS Propagation Takes Time
- Usually: 2-6 hours
- Maximum: 48 hours
- Check: https://dnschecker.org/

### 5. HTTPS is Automatic
Google Cloud Run automatically provisions SSL certificates. No configuration needed!

---

## 🆘 Troubleshooting

### "gcloud: command not found"

Install gcloud CLI:
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
```

### "Permission denied: deploy-to-cloud-run.sh"

Make executable:
```bash
chmod +x deploy-to-cloud-run.sh
```

### "Module not found" errors

Install dependencies:
```bash
pip install -r requirements.txt
cd frontend && npm install
```

### DNS not working

1. Verify A records in Namecheap match Google Cloud IPs
2. Check propagation: `dig elsontb.com`
3. Wait up to 48 hours for full propagation

### Deployment failing on GitHub Actions

1. Verify all 6 secrets are configured
2. Check workflow logs in GitHub Actions tab
3. Ensure GCP_SA_KEY is valid JSON

---

## 📊 Deployment Checklist

Before going live:

- [ ] GitHub secrets configured (if using automated deployment)
- [ ] Google Cloud project created
- [ ] Required APIs enabled
- [ ] Application deployed to Cloud Run
- [ ] DNS records added to Namecheap
- [ ] DNS propagation verified
- [ ] SSL certificate issued
- [ ] Application accessible at https://elsontb.com
- [ ] Can create account and login
- [ ] API endpoints working
- [ ] CORS configured for domain
- [ ] Monitoring set up (optional but recommended)

---

## 🎯 Next Steps After Deployment

1. **Test Thoroughly**
   - Create account
   - Place paper trades
   - Verify market data

2. **Set Up Monitoring**
   - UptimeRobot: https://uptimerobot.com/
   - Monitor: https://elsontb.com/health

3. **Upgrade Database** (Recommended for Production)
   - Switch from SQLite to Cloud SQL (PostgreSQL)
   - Better performance and reliability

4. **Enable Backups**
   - Set up automated database backups
   - Export configurations regularly

5. **Optimize**
   - Enable Redis caching
   - Configure CDN for frontend assets
   - Set up logging and analytics

---

## 📞 Need Help?

- **Deployment Issues:** See `DEPLOYMENT_GUIDE.md`
- **DNS Problems:** See `NAMECHEAP_DNS_SETUP.md`
- **GitHub Actions:** See `GITHUB_SECRETS_SETUP.md`
- **Local Setup:** See `SETUP_GUIDE.md`
- **API Reference:** https://elsontb.com/docs (after deployment)

---

## 🎉 Success Criteria

You'll know everything is working when:

✅ https://elsontb.com loads without certificate warnings
✅ Can register and login
✅ Can place paper trades
✅ Market data displays correctly
✅ API docs accessible at https://elsontb.com/docs
✅ Health check returns: `{"status":"healthy"}`

---

## ⏱️ Time Estimate

| Step | Time |
|------|------|
| Install gcloud CLI | 5 min (if needed) |
| Configure GitHub Secrets | 30 min (one-time) |
| Deploy to Cloud Run | 5 min |
| Configure Namecheap DNS | 15 min |
| **DNS Propagation** | **2-48 hours** ⏳ |
| SSL Certificate Provisioning | 15-30 min |
| **Total Active Time** | **~60 min** |

**Note:** Most of the time is waiting for DNS propagation, which happens automatically.

---

## 🚀 Ready to Deploy?

**Easiest path:**

1. Follow `GITHUB_SECRETS_SETUP.md` (30 min)
2. Push to main: `git push origin main`
3. Follow `NAMECHEAP_DNS_SETUP.md` (15 min)
4. Wait for DNS propagation (2-24 hours)
5. Visit https://elsontb.com 🎉

**Your trading platform will be live!**

---

**Questions?** Check the detailed guides or review `DEPLOYMENT_GUIDE.md` for all deployment options.

**Happy Trading! 📈**
