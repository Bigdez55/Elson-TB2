# Namecheap DNS Setup for Elsontb.com → Google Cloud Run

This guide walks you through connecting your Namecheap domain (Elsontb.com) to your Google Cloud Run deployment.

---

## Overview

**Goal:** Point `elsontb.com` and `www.elsontb.com` to your Google Cloud Run service

**Time Required:** 15 minutes setup + 24-48 hours DNS propagation

**What You'll Get:**
- ✅ Your app accessible at https://elsontb.com
- ✅ Automatic HTTPS (SSL certificate)
- ✅ www subdomain working
- ✅ Google-managed infrastructure

---

## Prerequisites

Before starting, make sure:
- ✅ Your app is deployed to Google Cloud Run
- ✅ You have access to your Namecheap account
- ✅ You have the Cloud Run service URL

---

## Step 1: Get Your Cloud Run Service URL

```bash
# Get your Cloud Run service URL
gcloud run services describe elson-trading-platform \
  --region us-central1 \
  --format='value(status.url)'
```

You should see something like:
```
https://elson-trading-platform-xxxxx-uc.a.run.app
```

**Save this URL** - you'll need it later.

---

## Step 2: Map Domain in Google Cloud Run

### 2.1 Map elsontb.com

```bash
gcloud run domain-mappings create \
  --service elson-trading-platform \
  --domain elsontb.com \
  --region us-central1
```

### 2.2 Map www.elsontb.com

```bash
gcloud run domain-mappings create \
  --service elson-trading-platform \
  --domain www.elsontb.com \
  --region us-central1
```

### 2.3 Verify Domain Mapping Status

```bash
gcloud run domain-mappings list --region us-central1
```

You should see both domains listed with status "Mapping...".

### 2.4 Get DNS Records

```bash
gcloud run domain-mappings describe elsontb.com \
  --region us-central1 \
  --format='value(status.resourceRecords)'
```

**Important:** Save the DNS records shown. You'll need them for Namecheap!

The output will look like:
```
NAME                    TYPE    DATA
elsontb.com             A       216.239.32.21
elsontb.com             A       216.239.34.21
elsontb.com             A       216.239.36.21
elsontb.com             A       216.239.38.21
elsontb.com             AAAA    2001:4860:4802:32::15
...
```

---

## Step 3: Configure DNS at Namecheap

### 3.1 Login to Namecheap

1. Go to https://www.namecheap.com/
2. Click **"Sign In"** (top right)
3. Enter your credentials

### 3.2 Navigate to Domain Management

1. Click **"Domain List"** in the left sidebar
2. Find **"Elsontb.com"**
3. Click **"Manage"** button

### 3.3 Access Advanced DNS

1. Click the **"Advanced DNS"** tab
2. You'll see your current DNS records

### 3.4 Remove Existing Records (if any)

**Before adding new records**, remove any existing:
- A Records pointing to old IPs
- CNAME Records for @ or www
- URL Redirect Records

Click the trash icon (🗑️) next to each old record.

### 3.5 Add Google Cloud Run A Records

Click **"Add New Record"** and add these **4 A Records**:

#### Record 1:
```
Type:  A Record
Host:  @
Value: 216.239.32.21
TTL:   Automatic
```

#### Record 2:
```
Type:  A Record
Host:  @
Value: 216.239.34.21
TTL:   Automatic
```

#### Record 3:
```
Type:  A Record
Host:  @
Value: 216.239.36.21
TTL:   Automatic
```

#### Record 4:
```
Type:  A Record
Host:  @
Value: 216.239.38.21
TTL:   Automatic
```

### 3.6 Add AAAA Records (IPv6 - Optional but Recommended)

Add these **4 AAAA Records** for IPv6 support:

#### Record 1:
```
Type:  AAAA Record
Host:  @
Value: 2001:4860:4802:32::15
TTL:   Automatic
```

#### Record 2:
```
Type:  AAAA Record
Host:  @
Value: 2001:4860:4802:34::15
TTL:   Automatic
```

#### Record 3:
```
Type:  AAAA Record
Host:  @
Value: 2001:4860:4802:36::15
TTL:   Automatic
```

#### Record 4:
```
Type:  AAAA Record
Host:  @
Value: 2001:4860:4802:38::15
TTL:   Automatic
```

### 3.7 Add CNAME for www

```
Type:  CNAME Record
Host:  www
Value: ghs.googlehosted.com.
TTL:   Automatic
```

**Note:** The trailing dot (`.`) after `com` is important!

### 3.8 Final DNS Configuration

Your Advanced DNS should look like this:

```
TYPE    HOST    VALUE                           TTL
──────────────────────────────────────────────────────────
A       @       216.239.32.21                   Automatic
A       @       216.239.34.21                   Automatic
A       @       216.239.36.21                   Automatic
A       @       216.239.38.21                   Automatic
AAAA    @       2001:4860:4802:32::15           Automatic
AAAA    @       2001:4860:4802:34::15           Automatic
AAAA    @       2001:4860:4802:36::15           Automatic
AAAA    @       2001:4860:4802:38::15           Automatic
CNAME   www     ghs.googlehosted.com.           Automatic
```

### 3.9 Save Changes

Click **"Save All Changes"** (green button at the top or bottom)

---

## Step 4: Wait for DNS Propagation

### 4.1 Understanding Propagation

- **Time Required:** Usually 15 minutes to 48 hours
- **Average:** 2-6 hours for most users
- **Why:** DNS changes need to propagate globally

### 4.2 Check Propagation Status

**Use these tools to check:**

1. **DNS Checker** (Recommended)
   - https://dnschecker.org/
   - Enter: `elsontb.com`
   - Select: `A` record type
   - Should show Google Cloud IPs globally

2. **Command Line:**
   ```bash
   # Check A records
   dig elsontb.com

   # Check CNAME for www
   dig www.elsontb.com

   # Check nameservers
   dig elsontb.com NS
   ```

3. **Online Tools:**
   - https://www.whatsmydns.net/
   - https://mxtoolbox.com/SuperTool.aspx

### 4.3 What You're Looking For

**Success indicators:**
- ✅ `elsontb.com` resolves to `216.239.32.21` (or one of the other Google IPs)
- ✅ `www.elsontb.com` resolves via CNAME to `ghs.googlehosted.com`
- ✅ Green checkmarks in most locations on dnschecker.org

---

## Step 5: Verify SSL Certificate

### 5.1 Check Certificate Status

```bash
gcloud run domain-mappings describe elsontb.com \
  --region us-central1 \
  --format='value(status.conditions[0].message)'
```

**Status meanings:**
- `"Ready"` = ✅ SSL certificate issued, domain working
- `"Mapping..."` = ⏳ Waiting for DNS propagation
- `"CertificatePending"` = ⏳ Waiting for Let's Encrypt to issue certificate

### 5.2 SSL Certificate Timeline

After DNS propagates:
1. Google detects DNS records (immediate)
2. Google requests Let's Encrypt certificate (1-5 minutes)
3. Let's Encrypt issues certificate (5-15 minutes)
4. Certificate deployed (immediate)

**Total:** Usually 15-30 minutes after DNS propagates

### 5.3 Test Your Site

```bash
# Test main domain
curl -I https://elsontb.com/health

# Test www subdomain
curl -I https://www.elsontb.com/health

# Or open in browser
open https://elsontb.com
```

**Expected response:**
```
HTTP/2 200
content-type: application/json
...
{"status":"healthy","service":"elson-trading-platform"}
```

---

## Step 6: Configure Backend CORS

Update your backend to allow your domain:

### 6.1 Update .env (Production)

```env
ALLOWED_ORIGINS=https://elsontb.com,https://www.elsontb.com,http://localhost:3000
```

### 6.2 Update Cloud Run Environment

```bash
gcloud run services update elson-trading-platform \
  --region us-central1 \
  --update-env-vars ALLOWED_ORIGINS="https://elsontb.com,https://www.elsontb.com"
```

---

## Troubleshooting

### Problem: DNS not propagating after 24 hours

**Check Namecheap nameservers:**
```bash
dig elsontb.com NS
```

Should show Namecheap nameservers like:
```
dns1.registrar-servers.com
dns2.registrar-servers.com
```

If different, you may need to update nameservers in Namecheap → Domain → Nameservers

### Problem: "Certificate Provisioning Failed"

**Causes:**
1. DNS not propagating yet → Wait longer
2. CAA records blocking Let's Encrypt → Remove CAA records in Namecheap
3. Too many certificate requests → Wait 1 hour and try again

**Solution:**
```bash
# Delete and recreate domain mapping
gcloud run domain-mappings delete elsontb.com --region us-central1
# Wait 5 minutes
gcloud run domain-mappings create --service elson-trading-platform --domain elsontb.com --region us-central1
```

### Problem: "Mixed Content" errors in browser

**Cause:** Frontend loading HTTP resources on HTTPS page

**Solution:** Update frontend to use HTTPS URLs:
```javascript
// Change
const API_URL = 'http://elsontb.com/api';

// To
const API_URL = 'https://elsontb.com/api';
```

### Problem: www subdomain not working

**Check CNAME:**
```bash
dig www.elsontb.com CNAME
```

Should return:
```
www.elsontb.com. 300 IN CNAME ghs.googlehosted.com.
```

If not, verify Namecheap CNAME record has trailing dot (`.`)

---

## Advanced: Email Configuration

If you want to use email with your domain (e.g., `info@elsontb.com`):

### Option 1: Google Workspace

1. Sign up at https://workspace.google.com/
2. Add MX records in Namecheap:

```
Type:  MX Record
Host:  @
Value: ASPMX.L.GOOGLE.COM
Priority: 1
TTL:   Automatic
```

### Option 2: Zoho Mail (Free)

1. Sign up at https://www.zoho.com/mail/
2. Add MX records from Zoho setup wizard

### Option 3: Forward to Existing Email

In Namecheap:
1. Advanced DNS → Email Forwarding
2. Add: `info@elsontb.com` → `your-email@gmail.com`

---

## Testing Checklist

After setup, verify:

- [ ] https://elsontb.com loads (no cert warnings)
- [ ] https://www.elsontb.com loads
- [ ] http://elsontb.com redirects to https://
- [ ] Can create account and login
- [ ] Can access API: https://elsontb.com/api/v1/...
- [ ] API docs work: https://elsontb.com/docs
- [ ] SSL certificate shows "Google Trust Services"
- [ ] No mixed content warnings in browser console

---

## DNS Records Reference

### Standard Setup (What We're Using)

```
# IPv4 (Required)
A     @     216.239.32.21
A     @     216.239.34.21
A     @     216.239.36.21
A     @     216.239.38.21

# IPv6 (Optional but recommended)
AAAA  @     2001:4860:4802:32::15
AAAA  @     2001:4860:4802:34::15
AAAA  @     2001:4860:4802:36::15
AAAA  @     2001:4860:4802:38::15

# WWW subdomain
CNAME www   ghs.googlehosted.com.
```

### Alternative: CNAME Setup (Not for apex domain)

**Note:** This only works for subdomains (e.g., `app.elsontb.com`), not the apex domain (`elsontb.com`).

```
CNAME app   ghs.googlehosted.com.
```

---

## Security: Force HTTPS

Google Cloud Run automatically redirects HTTP → HTTPS, but you can verify:

```bash
curl -I http://elsontb.com
```

Should show:
```
HTTP/1.1 301 Moved Permanently
Location: https://elsontb.com/
```

---

## Monitoring

### Set Up Uptime Monitoring

**Free options:**
1. **UptimeRobot** - https://uptimerobot.com/
   - Monitor: https://elsontb.com/health
   - Alert: Email/SMS if down

2. **Google Cloud Monitoring**
   ```bash
   # Enable monitoring
   gcloud services enable monitoring.googleapis.com

   # Create uptime check (via console)
   ```

3. **Pingdom** - https://www.pingdom.com/

---

## Cost Estimate

### Google Cloud Run

**Free tier (plenty for starting):**
- 2 million requests/month free
- 360,000 GB-seconds free
- 180,000 vCPU-seconds free

**After free tier:**
- ~$0.00001 per request
- ~$0.00002 per GB-second
- ~$0.00002 per vCPU-second

**Expected cost:** $0-5/month for low traffic

### SSL Certificate

- ✅ **FREE** (Google-managed Let's Encrypt)
- Auto-renewal
- No configuration needed

---

## Next Steps

After DNS is working:

1. ✅ Test your application thoroughly
2. ✅ Set up monitoring and alerts
3. ✅ Configure automated backups
4. ✅ Upgrade to Cloud SQL (PostgreSQL) for production
5. ✅ Set up CI/CD for automatic deployments
6. ✅ Configure email service

---

## Quick Reference Commands

```bash
# Check domain mapping status
gcloud run domain-mappings list --region us-central1

# Get DNS records for verification
gcloud run domain-mappings describe elsontb.com --region us-central1

# Update environment variables
gcloud run services update elson-trading-platform \
  --region us-central1 \
  --update-env-vars KEY=VALUE

# View logs
gcloud run services logs read elson-trading-platform --region us-central1

# Check DNS propagation
dig elsontb.com
dig www.elsontb.com
```

---

**🎉 Once configured, your platform will be live at:**

- **Main site:** https://elsontb.com
- **With www:** https://www.elsontb.com
- **API Docs:** https://elsontb.com/docs
- **Health:** https://elsontb.com/health

**DNS propagation takes time, but you're all set once it completes!** ⏳→✅
