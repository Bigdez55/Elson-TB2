#!/usr/bin/env python3
"""
Quick Authentication Test for Elson-TB2
"""

import sys
import requests
import json
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, "/workspaces/Elson-TB2/backend")

try:
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.config import settings
    
    print(f"🔍 Testing with database: {settings.DATABASE_URL}")
    
    client = TestClient(app)
    
    # Test user data
    test_email = f"test_user_{datetime.now().timestamp()}@example.com"
    test_password = "TestPassword123!"
    
    print("🚀 Starting quick authentication test...")
    
    # Test 1: User Registration
    print("\n1. Testing user registration...")
    reg_data = {
        "email": test_email,
        "password": test_password,
        "full_name": "Test User",
        "risk_tolerance": "moderate",
        "trading_style": "long_term"
    }
    
    reg_response = client.post("/api/v1/auth/register", json=reg_data)
    print(f"   Status: {reg_response.status_code}")
    
    if reg_response.status_code == 200:
        reg_data_response = reg_response.json()
        print(f"   ✅ Registration successful!")
        print(f"   User ID: {reg_data_response['user']['id']}")
        print(f"   Email: {reg_data_response['user']['email']}")
        print(f"   Token received: {'access_token' in reg_data_response}")
        
        # Test 2: User Login
        print("\n2. Testing user login...")
        login_data = {
            "email": test_email,
            "password": test_password
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        print(f"   Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_data_response = login_response.json()
            print(f"   ✅ Login successful!")
            print(f"   Token received: {'access_token' in login_data_response}")
            
            # Test 3: Protected endpoint
            print("\n3. Testing protected endpoint...")
            headers = {"Authorization": f"Bearer {login_data_response['access_token']}"}
            me_response = client.get("/api/v1/auth/me", headers=headers)
            print(f"   Status: {me_response.status_code}")
            
            if me_response.status_code == 200:
                me_data = me_response.json()
                print(f"   ✅ Protected endpoint access successful!")
                print(f"   User: {me_data['email']}")
            else:
                print(f"   ❌ Protected endpoint failed: {me_response.text}")
        else:
            print(f"   ❌ Login failed: {login_response.text}")
    else:
        print(f"   ❌ Registration failed: {reg_response.text}")
    
    # Test 4: Invalid login
    print("\n4. Testing invalid login...")
    invalid_login = {
        "email": test_email,
        "password": "WrongPassword"
    }
    
    invalid_response = client.post("/api/v1/auth/login", json=invalid_login)
    print(f"   Status: {invalid_response.status_code}")
    
    if invalid_response.status_code == 401:
        print(f"   ✅ Invalid login correctly rejected!")
    else:
        print(f"   ❌ Invalid login not properly handled: {invalid_response.text}")
    
    print("\n✅ Authentication test completed!")
    
except Exception as e:
    print(f"❌ Test failed with error: {e}")
    import traceback
    traceback.print_exc()