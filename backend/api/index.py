import sys
import os

# Add the parent directory to Python path so we can import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

# Vercel serverless function handler
# This exports the FastAPI app for Vercel to use
handler = app
