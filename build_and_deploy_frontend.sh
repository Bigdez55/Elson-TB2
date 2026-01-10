#!/bin/bash
set -e

# Frontend deployment script for Elson Trading Platform

# Configuration
PROJECT_ID="elson-33a95"
REGION="us-central1"
SERVICE_NAME="elson-frontend"
BACKEND_URL="https://elson-backend-490677787763.us-central1.run.app"

# 1. Build the frontend with the correct API URL
echo "Building frontend..."
cd frontend
npm install --legacy-peer-deps
REACT_APP_API_URL=$BACKEND_URL/api/v1 npm run build
cd ..

# 2. Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --source ./frontend \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --project $PROJECT_ID
