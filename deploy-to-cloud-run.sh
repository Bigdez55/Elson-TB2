#!/bin/bash

# Elson Trading Platform - Google Cloud Run Deployment Script
# This script automates the deployment of your platform to Google Cloud Run

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Elson Trading Platform - Cloud Run Deployment       ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Error: gcloud CLI is not installed${NC}"
    echo ""
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    echo ""
    echo "Quick install (Linux/macOS):"
    echo "  curl https://sdk.cloud.google.com | bash"
    echo "  exec -l \$SHELL"
    echo "  gcloud init"
    exit 1
fi

echo -e "${GREEN}✅ Google Cloud CLI found${NC}"
echo ""

# Project Configuration
echo -e "${YELLOW}📋 Project Configuration${NC}"
echo ""

# Check if already logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${YELLOW}Please login to Google Cloud:${NC}"
    gcloud auth login
fi

echo -e "${GREEN}✅ Logged in to Google Cloud${NC}"
echo ""

# Get or set project ID
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")

if [ -z "$CURRENT_PROJECT" ]; then
    echo -e "${YELLOW}No project selected. Let's set one up.${NC}"
    echo ""
    read -p "Enter your Google Cloud Project ID (or press Enter to create a new one): " PROJECT_ID

    if [ -z "$PROJECT_ID" ]; then
        # Generate a unique project ID
        RANDOM_SUFFIX=$(date +%s | tail -c 5)
        PROJECT_ID="elson-trading-${RANDOM_SUFFIX}"
        echo -e "${BLUE}Creating new project: ${PROJECT_ID}${NC}"
        gcloud projects create $PROJECT_ID --name="Elson Trading Platform"
    fi

    gcloud config set project $PROJECT_ID
else
    PROJECT_ID=$CURRENT_PROJECT
    echo -e "${GREEN}Using existing project: ${PROJECT_ID}${NC}"
fi

echo ""
echo -e "${BLUE}Project ID: ${PROJECT_ID}${NC}"
echo ""

# Set region
REGION="us-central1"
echo -e "${BLUE}Region: ${REGION}${NC}"
gcloud config set run/region $REGION
echo ""

# Enable required APIs
echo -e "${YELLOW}🔧 Enabling required Google Cloud APIs...${NC}"
echo "This may take a few minutes..."
echo ""

gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable sqladmin.googleapis.com

echo -e "${GREEN}✅ APIs enabled${NC}"
echo ""

# Build and deploy
echo -e "${YELLOW}🏗️  Building and deploying your application...${NC}"
echo ""

# Submit build using Cloud Build
echo "Submitting build to Cloud Build..."
gcloud builds submit --config cloudbuild.yaml

echo ""
echo -e "${GREEN}✅ Build completed successfully!${NC}"
echo ""

# Get the service URL
echo -e "${YELLOW}🌐 Getting service URL...${NC}"
SERVICE_URL=$(gcloud run services describe elson-trading-platform \
  --platform=managed \
  --region=$REGION \
  --format='value(status.url)' 2>/dev/null || echo "")

if [ -z "$SERVICE_URL" ]; then
    echo -e "${RED}❌ Could not retrieve service URL${NC}"
    echo "Please check Cloud Run console: https://console.cloud.google.com/run"
else
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║            🎉 DEPLOYMENT SUCCESSFUL! 🎉                ║${NC}"
    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo ""
    echo -e "${BLUE}Your application is now live at:${NC}"
    echo -e "${GREEN}${SERVICE_URL}${NC}"
    echo ""
    echo -e "${BLUE}API Documentation:${NC}"
    echo -e "${GREEN}${SERVICE_URL}/docs${NC}"
    echo ""
    echo -e "${BLUE}Health Check:${NC}"
    echo -e "${GREEN}${SERVICE_URL}/health${NC}"
    echo ""
fi

# Custom domain setup
echo -e "${YELLOW}🌐 Custom Domain Setup${NC}"
echo ""
echo "To use your domain (elsontb.com), follow these steps:"
echo ""
echo "1. Map your domain in Cloud Run:"
echo "   gcloud run domain-mappings create --service elson-trading-platform --domain elsontb.com --region=${REGION}"
echo ""
echo "2. Configure DNS at Namecheap (see NAMECHEAP_DNS_SETUP.md for details)"
echo ""
echo "3. SSL will be automatically provisioned by Google (takes 15 minutes)"
echo ""

# Environment variables
echo -e "${YELLOW}⚙️  Important: Environment Variables${NC}"
echo ""
echo "Make sure to set these environment variables in Cloud Run:"
echo "  - SECRET_KEY"
echo "  - ALPHA_VANTAGE_API_KEY"
echo "  - ALPACA_API_KEY"
echo "  - ALPACA_SECRET_KEY"
echo "  - ENVIRONMENT=production"
echo "  - DEBUG=false"
echo ""
echo "Update them with:"
echo "  gcloud run services update elson-trading-platform \\"
echo "    --region=${REGION} \\"
echo "    --update-env-vars SECRET_KEY=your-secret-key,ENVIRONMENT=production"
echo ""

# Database recommendation
echo -e "${YELLOW}💾 Database Setup${NC}"
echo ""
echo "For production, consider Cloud SQL (PostgreSQL):"
echo "  - More reliable than SQLite"
echo "  - Automatic backups"
echo "  - Better performance"
echo ""
echo "Run: ./setup-cloud-sql.sh (coming soon)"
echo ""

echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Deployment Complete! 🚀                   ║${NC}"
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo ""
echo "Next steps:"
echo "  1. Configure environment variables (see above)"
echo "  2. Set up custom domain (elsontb.com)"
echo "  3. Configure Cloud SQL (recommended)"
echo "  4. Set up monitoring and alerting"
echo ""
echo "Documentation: DEPLOYMENT_GUIDE.md"
echo ""
