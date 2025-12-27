#!/bin/bash

# Production Deployment Script for Elson Trading Platform
# Domain: elsontb.com
# Run this script to deploy to Google Cloud Run

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${PROJECT_ID:-"your-gcp-project-id"}
REGION=${REGION:-"us-central1"}
BACKEND_SERVICE=${BACKEND_SERVICE:-"elson-backend"}
FRONTEND_SERVICE=${FRONTEND_SERVICE:-"elson-frontend"}

echo -e "${BLUE}🚀 Starting production deployment for Elson Trading Platform${NC}"
echo -e "${BLUE}Domain: elsontb.com${NC}"
echo -e "${BLUE}Project: $PROJECT_ID${NC}"
echo -e "${BLUE}Region: $REGION${NC}"

# Validate prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ Not authenticated with gcloud. Please run 'gcloud auth login'${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites met${NC}"

# Set project
echo -e "${YELLOW}🔧 Setting GCP project...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW}🔧 Enabling required APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com

# Build and deploy using Cloud Build
echo -e "${YELLOW}🏗️ Building and deploying with Cloud Build...${NC}"
gcloud builds submit --config cloudbuild.yaml .

# Get service URLs
echo -e "${YELLOW}📡 Getting service URLs...${NC}"
BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE --region=$REGION --format="value(status.url)")
FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE --region=$REGION --format="value(status.url)")

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}🌐 Backend URL: $BACKEND_URL${NC}"
echo -e "${GREEN}🌐 Frontend URL: $FRONTEND_URL${NC}"

# Domain mapping instructions
echo -e "${YELLOW}"
echo "📝 To complete the deployment with custom domain (elsontb.com):"
echo "1. Set up domain mapping in Google Cloud Console"
echo "2. Point your DNS to the provided URLs"
echo "3. Configure SSL certificates"
echo ""
echo "Backend (API): $BACKEND_URL"
echo "Frontend (Web): $FRONTEND_URL"
echo ""
echo "For custom domain setup, run:"
echo "gcloud run domain-mappings create --service=$FRONTEND_SERVICE --domain=elsontb.com --region=$REGION"
echo "gcloud run domain-mappings create --service=$BACKEND_SERVICE --domain=api.elsontb.com --region=$REGION"
echo -e "${NC}"

# Health checks
echo -e "${YELLOW}🏥 Running health checks...${NC}"
echo "Backend health: $BACKEND_URL/health"
echo "Frontend health: $FRONTEND_URL/health"

# Test backend health
if curl -f "$BACKEND_URL/health" &> /dev/null; then
    echo -e "${GREEN}✅ Backend is healthy${NC}"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
fi

# Test frontend health
if curl -f "$FRONTEND_URL/health" &> /dev/null; then
    echo -e "${GREEN}✅ Frontend is healthy${NC}"
else
    echo -e "${RED}❌ Frontend health check failed${NC}"
fi

echo -e "${GREEN}🎉 Production deployment complete!${NC}"