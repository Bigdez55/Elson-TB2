# Deployment Guide for Elson Trading Platform

## Vercel Deployment (Frontend)

### Prerequisites
- GitHub account connected to Vercel
- Backend API deployed and accessible

### Step 1: Configure Vercel Project

1. Go to your Vercel dashboard
2. Import the `Elson-TB2` repository from GitHub
3. Vercel will automatically detect the configuration from `vercel.json`

### Step 2: Set Environment Variables

In your Vercel project settings, add the following environment variable:

| Variable Name | Value | Description |
|---------------|-------|-------------|
| `REACT_APP_API_URL` | Your backend API URL | Example: `https://your-backend.herokuapp.com/api/v1` |

**Important:** Make sure to set this for the **Production** environment.

### Step 3: Deploy

1. Push your changes to the `main` branch (or your default branch)
2. Vercel will automatically build and deploy your frontend
3. The build command will run: `cd frontend && npm install && npm run build`
4. Output will be served from: `frontend/build`

### Step 4: Verify Deployment

After deployment completes:

1. Visit your Vercel URL (e.g., `https://elson-tb-2.vercel.app`)
2. Test the login and registration pages
3. Verify the styling matches the dashboard theme
4. Test API connectivity by attempting to register/login

## Backend Deployment

The backend (FastAPI) needs to be deployed separately. Recommended options:

### Option 1: Heroku
```bash
# From the project root
cd backend
git init
heroku create your-backend-name
git add .
git commit -m "Deploy backend"
git push heroku main
```

### Option 2: Railway
1. Connect your GitHub repo to Railway
2. Select the `backend` directory as the root
3. Railway will auto-detect FastAPI and deploy

### Option 3: Vercel (Python)
1. Add a `vercel.json` in the `backend` directory
2. Configure it for Python/FastAPI deployment
3. Deploy separately from the frontend

## Environment Variables (Backend)

Make sure your backend has these environment variables configured:

- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT secret key
- `ALLOWED_ORIGINS` - Frontend URL (e.g., `https://elson-tb-2.vercel.app`)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time

## CORS Configuration

Ensure your backend's CORS settings allow requests from your Vercel frontend URL:

```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://elson-tb-2.vercel.app"],  # Add your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Troubleshooting

### Registration/Login Fails
- Check browser console for API errors
- Verify `REACT_APP_API_URL` is set correctly in Vercel
- Ensure backend CORS allows your frontend URL
- Verify backend is running and accessible

### Styling Issues
- Clear browser cache
- Check that the build deployed successfully
- Verify Tailwind CSS is building properly

### Build Fails
- Check Vercel build logs
- Ensure all dependencies are in `package.json`
- Verify Node version compatibility

## Custom Domain (Optional)

To add a custom domain:

1. Go to Vercel project settings → Domains
2. Add your custom domain
3. Configure DNS records as shown by Vercel
4. Update CORS settings in backend to include custom domain

## Monitoring

After deployment, monitor:
- Vercel Analytics for frontend performance
- Backend logs for API errors
- User registration/login success rates
- Error tracking (consider adding Sentry)

## Updates

To deploy updates:

1. Push changes to your GitHub repository
2. Vercel will automatically rebuild and deploy
3. No manual intervention needed

---

**Need help?** Check the Vercel documentation at https://vercel.com/docs
