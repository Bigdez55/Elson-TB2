#!/usr/bin/env python3
"""
Comprehensive Authentication and Database Testing for Elson-TB2
"""

import json
import os
import sqlite3
import sys
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

# Add the app directory to Python path
sys.path.insert(0, "/workspaces/Elson-TB2/backend")

try:
    import bcrypt
    import jwt as pyjwt
    import pytest
    import redis
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    from app.core.config import settings
    from app.core.security import (
        create_access_token,
        get_password_hash,
        redis_client,
        verify_password,
        verify_token,
    )
    from app.db.base import SessionLocal, engine, get_db

    # Import app components
    from app.main import app
    from app.models.user import User, UserRole

except ImportError as e:
    print(f"Import error: {e}")
    print("Installing required packages...")
    os.system("pip install fastapi pytest pytest-asyncio sqlalchemy bcrypt PyJWT redis")
    sys.exit(1)


class AuthDatabaseTester:
    def __init__(self):
        self.client = TestClient(app)
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "database_tests": {},
            "auth_tests": {},
            "security_tests": {},
            "issues": [],
            "recommendations": [],
        }

    def log_test(self, category: str, test_name: str, status: str, details: Any = None):
        """Log test results"""
        if category not in self.test_results:
            self.test_results[category] = {}

        self.test_results[category][test_name] = {
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }

        if status == "FAILED":
            self.test_results["issues"].append(f"{category}.{test_name}: {details}")

    def test_database_connectivity(self):
        """Test 1: Database connectivity and configuration"""
        print("🔍 Testing database connectivity...")

        try:
            # Test basic connection
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                assert result.fetchone()[0] == 1

            self.log_test(
                "database_tests",
                "basic_connectivity",
                "PASSED",
                "Database connection successful",
            )

            # Test database path and permissions
            db_path = settings.DATABASE_URL.replace("sqlite:///", "")
            if os.path.exists(db_path):
                file_size = os.path.getsize(db_path)
                self.log_test(
                    "database_tests",
                    "file_access",
                    "PASSED",
                    f"Database file exists, size: {file_size} bytes",
                )
            else:
                self.log_test(
                    "database_tests",
                    "file_access",
                    "FAILED",
                    f"Database file not found at {db_path}",
                )

        except Exception as e:
            self.log_test("database_tests", "basic_connectivity", "FAILED", str(e))

    def test_database_schema(self):
        """Test 2: Database schema validation"""
        print("🔍 Testing database schema...")

        try:
            with engine.connect() as connection:
                # Check if users table exists
                result = connection.execute(
                    text(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
                    )
                )
                tables = result.fetchall()

                if tables:
                    self.log_test(
                        "database_tests",
                        "users_table_exists",
                        "PASSED",
                        "Users table found",
                    )

                    # Check user table structure
                    result = connection.execute(text("PRAGMA table_info(users)"))
                    columns = {row[1]: row[2] for row in result.fetchall()}

                    required_columns = [
                        "id",
                        "email",
                        "hashed_password",
                        "full_name",
                        "is_active",
                        "is_verified",
                        "created_at",
                    ]

                    missing_columns = [
                        col for col in required_columns if col not in columns
                    ]
                    if missing_columns:
                        self.log_test(
                            "database_tests",
                            "schema_validation",
                            "FAILED",
                            f"Missing columns: {missing_columns}",
                        )
                    else:
                        self.log_test(
                            "database_tests",
                            "schema_validation",
                            "PASSED",
                            f"All required columns present: {list(columns.keys())}",
                        )
                else:
                    self.log_test(
                        "database_tests",
                        "users_table_exists",
                        "FAILED",
                        "Users table not found",
                    )

        except Exception as e:
            self.log_test("database_tests", "schema_validation", "FAILED", str(e))

    def test_password_hashing(self):
        """Test 3: Password hashing and verification"""
        print("🔍 Testing password hashing...")

        try:
            test_password = "TestPassword123!"

            # Test hashing
            hashed = get_password_hash(test_password)
            if hashed and len(hashed) > 50:  # bcrypt hashes are typically ~60 chars
                self.log_test(
                    "auth_tests",
                    "password_hashing",
                    "PASSED",
                    f"Password hashed successfully, length: {len(hashed)}",
                )
            else:
                self.log_test(
                    "auth_tests",
                    "password_hashing",
                    "FAILED",
                    "Password hash appears invalid",
                )

            # Test verification
            if verify_password(test_password, hashed):
                self.log_test(
                    "auth_tests",
                    "password_verification",
                    "PASSED",
                    "Password verification successful",
                )
            else:
                self.log_test(
                    "auth_tests",
                    "password_verification",
                    "FAILED",
                    "Password verification failed",
                )

            # Test wrong password
            if not verify_password("WrongPassword", hashed):
                self.log_test(
                    "auth_tests",
                    "password_rejection",
                    "PASSED",
                    "Wrong password correctly rejected",
                )
            else:
                self.log_test(
                    "auth_tests",
                    "password_rejection",
                    "FAILED",
                    "Wrong password incorrectly accepted",
                )

        except Exception as e:
            self.log_test("auth_tests", "password_hashing", "FAILED", str(e))

    def test_jwt_tokens(self):
        """Test 4: JWT token generation and validation"""
        print("🔍 Testing JWT token functionality...")

        try:
            test_email = "test@example.com"

            # Test token creation
            token = create_access_token(data={"sub": test_email})
            if token and len(token) > 50:
                self.log_test(
                    "auth_tests",
                    "jwt_creation",
                    "PASSED",
                    f"JWT token created, length: {len(token)}",
                )
            else:
                self.log_test(
                    "auth_tests", "jwt_creation", "FAILED", "JWT token creation failed"
                )
                return

            # Test token verification
            payload = verify_token(token)
            if payload and payload.get("sub") == test_email:
                self.log_test(
                    "auth_tests",
                    "jwt_verification",
                    "PASSED",
                    f"JWT token verified, payload: {payload}",
                )
            else:
                self.log_test(
                    "auth_tests",
                    "jwt_verification",
                    "FAILED",
                    f"JWT token verification failed, payload: {payload}",
                )

            # Test token expiration
            expired_token = create_access_token(
                data={"sub": test_email}, expires_delta=timedelta(seconds=-1)
            )
            expired_payload = verify_token(expired_token)
            if not expired_payload:
                self.log_test(
                    "auth_tests",
                    "jwt_expiration",
                    "PASSED",
                    "Expired token correctly rejected",
                )
            else:
                self.log_test(
                    "auth_tests",
                    "jwt_expiration",
                    "FAILED",
                    "Expired token incorrectly accepted",
                )

        except Exception as e:
            self.log_test("auth_tests", "jwt_tokens", "FAILED", str(e))

    def test_user_registration(self):
        """Test 5: User registration flow"""
        print("🔍 Testing user registration...")

        try:
            test_user_data = {
                "email": f"test_user_{datetime.now().timestamp()}@example.com",
                "password": "TestPassword123!",
                "full_name": "Test User",
                "risk_tolerance": "moderate",
                "trading_style": "long_term",
            }

            response = self.client.post("/api/v1/auth/register", json=test_user_data)

            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    self.log_test(
                        "auth_tests",
                        "user_registration",
                        "PASSED",
                        f"User registered successfully, user_id: {data['user']['id']}",
                    )

                    # Test duplicate registration
                    duplicate_response = self.client.post(
                        "/api/v1/auth/register", json=test_user_data
                    )
                    if duplicate_response.status_code == 400:
                        self.log_test(
                            "auth_tests",
                            "duplicate_registration_prevention",
                            "PASSED",
                            "Duplicate registration correctly prevented",
                        )
                    else:
                        self.log_test(
                            "auth_tests",
                            "duplicate_registration_prevention",
                            "FAILED",
                            f"Duplicate registration not prevented: {duplicate_response.status_code}",
                        )
                else:
                    self.log_test(
                        "auth_tests",
                        "user_registration",
                        "FAILED",
                        f"Registration response missing required fields: {data}",
                    )
            else:
                self.log_test(
                    "auth_tests",
                    "user_registration",
                    "FAILED",
                    f"Registration failed with status {response.status_code}: {response.text}",
                )

        except Exception as e:
            self.log_test("auth_tests", "user_registration", "FAILED", str(e))

    def test_user_login(self):
        """Test 6: User login flow"""
        print("🔍 Testing user login...")

        try:
            # First register a user
            test_user_data = {
                "email": f"login_test_{datetime.now().timestamp()}@example.com",
                "password": "TestPassword123!",
                "full_name": "Login Test User",
            }

            reg_response = self.client.post(
                "/api/v1/auth/register", json=test_user_data
            )
            if reg_response.status_code != 200:
                self.log_test(
                    "auth_tests",
                    "login_test_setup",
                    "FAILED",
                    "Could not create test user for login test",
                )
                return

            # Test successful login
            login_data = {
                "email": test_user_data["email"],
                "password": test_user_data["password"],
            }

            login_response = self.client.post("/api/v1/auth/login", json=login_data)

            if login_response.status_code == 200:
                data = login_response.json()
                if "access_token" in data and "user" in data:
                    self.log_test(
                        "auth_tests", "user_login", "PASSED", f"User login successful"
                    )

                    # Test token usage
                    headers = {"Authorization": f"Bearer {data['access_token']}"}
                    me_response = self.client.get("/api/v1/auth/me", headers=headers)

                    if me_response.status_code == 200:
                        self.log_test(
                            "auth_tests",
                            "token_usage",
                            "PASSED",
                            "Token successfully used for authenticated request",
                        )
                    else:
                        self.log_test(
                            "auth_tests",
                            "token_usage",
                            "FAILED",
                            f"Token usage failed: {me_response.status_code}",
                        )
                else:
                    self.log_test(
                        "auth_tests",
                        "user_login",
                        "FAILED",
                        f"Login response missing required fields: {data}",
                    )
            else:
                self.log_test(
                    "auth_tests",
                    "user_login",
                    "FAILED",
                    f"Login failed with status {login_response.status_code}: {login_response.text}",
                )

            # Test failed login
            wrong_login_data = {
                "email": test_user_data["email"],
                "password": "WrongPassword",
            }

            wrong_response = self.client.post(
                "/api/v1/auth/login", json=wrong_login_data
            )
            if wrong_response.status_code == 401:
                self.log_test(
                    "auth_tests",
                    "failed_login_handling",
                    "PASSED",
                    "Wrong password correctly rejected",
                )
            else:
                self.log_test(
                    "auth_tests",
                    "failed_login_handling",
                    "FAILED",
                    f"Wrong password not properly rejected: {wrong_response.status_code}",
                )

        except Exception as e:
            self.log_test("auth_tests", "user_login", "FAILED", str(e))

    def test_redis_connectivity(self):
        """Test 7: Redis connectivity for session management"""
        print("🔍 Testing Redis connectivity...")

        try:
            if redis_client:
                # Test Redis connection
                redis_client.ping()
                self.log_test(
                    "database_tests",
                    "redis_connectivity",
                    "PASSED",
                    "Redis connection successful",
                )

                # Test Redis operations
                test_key = f"test_key_{datetime.now().timestamp()}"
                redis_client.setex(test_key, 10, "test_value")

                value = redis_client.get(test_key)
                if value and value.decode() == "test_value":
                    self.log_test(
                        "database_tests",
                        "redis_operations",
                        "PASSED",
                        "Redis read/write operations successful",
                    )
                else:
                    self.log_test(
                        "database_tests",
                        "redis_operations",
                        "FAILED",
                        "Redis read/write operations failed",
                    )

                # Cleanup
                redis_client.delete(test_key)
            else:
                self.log_test(
                    "database_tests",
                    "redis_connectivity",
                    "WARNING",
                    "Redis client not available - session management limited",
                )

        except Exception as e:
            self.log_test("database_tests", "redis_connectivity", "FAILED", str(e))

    def test_rate_limiting(self):
        """Test 8: Rate limiting functionality"""
        print("🔍 Testing rate limiting...")

        try:
            test_email = f"rate_test_{datetime.now().timestamp()}@example.com"

            # Register a test user first
            reg_response = self.client.post(
                "/api/v1/auth/register",
                json={
                    "email": test_email,
                    "password": "TestPassword123!",
                    "full_name": "Rate Test User",
                },
            )

            if reg_response.status_code != 200:
                self.log_test(
                    "security_tests",
                    "rate_limiting_setup",
                    "FAILED",
                    "Could not create test user for rate limiting test",
                )
                return

            # Test multiple failed login attempts
            failed_attempts = 0
            for i in range(10):  # Try 10 failed logins
                response = self.client.post(
                    "/api/v1/auth/login",
                    json={"email": test_email, "password": "WrongPassword"},
                )

                if response.status_code == 429:  # Too Many Requests
                    self.log_test(
                        "security_tests",
                        "rate_limiting",
                        "PASSED",
                        f"Rate limiting activated after {i} failed attempts",
                    )
                    break
                elif response.status_code == 401:
                    failed_attempts += 1
                    continue
                else:
                    break

            if failed_attempts >= 10:
                self.log_test(
                    "security_tests",
                    "rate_limiting",
                    "WARNING",
                    "Rate limiting not activated after 10 failed attempts",
                )

        except Exception as e:
            self.log_test("security_tests", "rate_limiting", "FAILED", str(e))

    def test_database_connections_pool(self):
        """Test 9: Database connection pool behavior"""
        print("🔍 Testing database connection pool...")

        try:
            # Test multiple concurrent connections
            connections = []
            for i in range(5):
                try:
                    db = SessionLocal()
                    # Test a simple query
                    result = db.execute(text("SELECT 1")).fetchone()
                    if result[0] == 1:
                        connections.append(db)
                    else:
                        db.close()
                        self.log_test(
                            "database_tests",
                            "connection_pool",
                            "FAILED",
                            f"Connection {i} failed query test",
                        )
                        return
                except Exception as e:
                    self.log_test(
                        "database_tests",
                        "connection_pool",
                        "FAILED",
                        f"Connection {i} failed: {str(e)}",
                    )
                    return

            # Close all connections
            for db in connections:
                db.close()

            self.log_test(
                "database_tests",
                "connection_pool",
                "PASSED",
                f"Successfully created and closed {len(connections)} connections",
            )

        except Exception as e:
            self.log_test("database_tests", "connection_pool", "FAILED", str(e))

    def test_security_configurations(self):
        """Test 10: Security configuration validation"""
        print("🔍 Testing security configurations...")

        try:
            # Check secret key strength
            if len(settings.SECRET_KEY) >= 32:
                self.log_test(
                    "security_tests",
                    "secret_key_strength",
                    "PASSED",
                    f"Secret key length: {len(settings.SECRET_KEY)}",
                )
            else:
                self.log_test(
                    "security_tests",
                    "secret_key_strength",
                    "FAILED",
                    f"Secret key too short: {len(settings.SECRET_KEY)} chars",
                )

            # Check default secret key
            if settings.SECRET_KEY == "your-secret-key-change-in-production":
                self.log_test(
                    "security_tests",
                    "default_secret_key",
                    "FAILED",
                    "Using default secret key - security risk!",
                )
            else:
                self.log_test(
                    "security_tests",
                    "default_secret_key",
                    "PASSED",
                    "Custom secret key configured",
                )

            # Check token expiration
            if settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0:
                self.log_test(
                    "security_tests",
                    "token_expiration",
                    "PASSED",
                    f"Token expiration: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes",
                )
            else:
                self.log_test(
                    "security_tests",
                    "token_expiration",
                    "FAILED",
                    "Token expiration not configured",
                )

            # Check CORS settings
            if "*" in settings.ALLOWED_ORIGINS:
                self.log_test(
                    "security_tests",
                    "cors_configuration",
                    "WARNING",
                    "CORS allows all origins - potential security risk in production",
                )
            else:
                self.log_test(
                    "security_tests",
                    "cors_configuration",
                    "PASSED",
                    f"CORS properly configured: {settings.ALLOWED_ORIGINS}",
                )

        except Exception as e:
            self.log_test("security_tests", "security_configurations", "FAILED", str(e))

    def check_existing_users(self):
        """Test 11: Check existing users and data integrity"""
        print("🔍 Checking existing users...")

        try:
            db = SessionLocal()
            users = db.query(User).all()

            user_count = len(users)
            self.log_test(
                "database_tests",
                "existing_users_count",
                "INFO",
                f"Found {user_count} existing users",
            )

            if user_count > 0:
                # Check user data integrity
                valid_users = 0
                for user in users:
                    if user.email and user.hashed_password and user.id:
                        valid_users += 1
                    else:
                        self.log_test(
                            "database_tests",
                            "user_data_integrity",
                            "WARNING",
                            f"User {user.id} has missing critical data",
                        )

                if valid_users == user_count:
                    self.log_test(
                        "database_tests",
                        "user_data_integrity",
                        "PASSED",
                        f"All {user_count} users have valid data",
                    )
                else:
                    self.log_test(
                        "database_tests",
                        "user_data_integrity",
                        "FAILED",
                        f"Only {valid_users}/{user_count} users have valid data",
                    )

            db.close()

        except Exception as e:
            self.log_test("database_tests", "existing_users_check", "FAILED", str(e))

    def test_two_factor_auth_readiness(self):
        """Test 12: Two-factor authentication readiness"""
        print("🔍 Testing 2FA readiness...")

        try:
            # Check if 2FA fields exist in user model
            db = SessionLocal()

            # Try to query 2FA field
            result = db.execute(text("PRAGMA table_info(users)"))
            columns = {row[1]: row[2] for row in result.fetchall()}

            if "two_factor_enabled" in columns:
                self.log_test(
                    "security_tests",
                    "2fa_database_ready",
                    "PASSED",
                    "Two-factor authentication field exists in database",
                )

                # Check if any users have 2FA enabled
                users_with_2fa = db.execute(
                    text("SELECT COUNT(*) FROM users WHERE two_factor_enabled = 1")
                ).fetchone()[0]
                self.log_test(
                    "security_tests",
                    "2fa_usage",
                    "INFO",
                    f"{users_with_2fa} users have 2FA enabled",
                )
            else:
                self.log_test(
                    "security_tests",
                    "2fa_database_ready",
                    "FAILED",
                    "Two-factor authentication field missing from database",
                )

            db.close()

        except Exception as e:
            self.log_test("security_tests", "2fa_readiness", "FAILED", str(e))

    def generate_recommendations(self):
        """Generate security and improvement recommendations"""
        print("🔍 Generating recommendations...")

        recommendations = []

        # Check for common issues and generate recommendations
        if any(
            "FAILED" in test.get("status", "")
            for test in self.test_results.get("database_tests", {}).values()
        ):
            recommendations.append(
                "Database connectivity issues detected - check connection strings and database file permissions"
            )

        if any(
            "FAILED" in test.get("status", "")
            for test in self.test_results.get("auth_tests", {}).values()
        ):
            recommendations.append(
                "Authentication system issues detected - review JWT configuration and password hashing"
            )

        if settings.SECRET_KEY == "your-secret-key-change-in-production":
            recommendations.append("CRITICAL: Change default secret key in production")

        if len(settings.SECRET_KEY) < 32:
            recommendations.append("Use a stronger secret key (minimum 32 characters)")

        if "*" in settings.ALLOWED_ORIGINS:
            recommendations.append("Restrict CORS origins for production deployment")

        if not redis_client:
            recommendations.append(
                "Configure Redis for better session management and rate limiting"
            )

        # Database-specific recommendations
        if settings.DATABASE_URL.startswith("sqlite"):
            recommendations.append(
                "Consider migrating to PostgreSQL for production use"
            )

        recommendations.extend(
            [
                "Implement comprehensive logging for security events",
                "Set up monitoring for failed authentication attempts",
                "Consider implementing account lockout policies",
                "Add email verification for new user registrations",
                "Implement password complexity requirements",
                "Set up regular security audits and penetration testing",
            ]
        )

        self.test_results["recommendations"] = recommendations

    def run_all_tests(self):
        """Run all authentication and database tests"""
        print("🚀 Starting comprehensive authentication and database testing...")
        print("=" * 60)

        # Run all test methods
        test_methods = [
            self.test_database_connectivity,
            self.test_database_schema,
            self.test_password_hashing,
            self.test_jwt_tokens,
            self.test_user_registration,
            self.test_user_login,
            self.test_redis_connectivity,
            self.test_rate_limiting,
            self.test_database_connections_pool,
            self.test_security_configurations,
            self.check_existing_users,
            self.test_two_factor_auth_readiness,
        ]

        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ Error in {test_method.__name__}: {e}")
                self.log_test("system_tests", test_method.__name__, "ERROR", str(e))

        # Generate recommendations
        self.generate_recommendations()

        print("\n" + "=" * 60)
        print("🏁 Testing completed!")
        return self.test_results


def main():
    """Main function to run the comprehensive test suite"""
    tester = AuthDatabaseTester()
    results = tester.run_all_tests()

    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"auth_database_test_results_{timestamp}.json"

    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Print summary
    print(f"\n📊 Test Results Summary:")
    print(f"{'='*50}")

    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    warnings = 0

    for category, tests in results.items():
        if isinstance(tests, dict) and category.endswith("_tests"):
            for test_name, test_result in tests.items():
                total_tests += 1
                status = test_result.get("status", "UNKNOWN")
                if status == "PASSED":
                    passed_tests += 1
                elif status == "FAILED":
                    failed_tests += 1
                elif status == "WARNING":
                    warnings += 1

                print(f"{status:8} | {category:15} | {test_name}")

    print(f"{'='*50}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    print(f"Warnings: {warnings} ⚠️")

    if results.get("issues"):
        print(f"\n🚨 Critical Issues Found ({len(results['issues'])}):")
        for issue in results["issues"]:
            print(f"  • {issue}")

    if results.get("recommendations"):
        print(f"\n💡 Recommendations ({len(results['recommendations'])}):")
        for i, rec in enumerate(results["recommendations"][:5], 1):  # Show top 5
            print(f"  {i}. {rec}")

        if len(results["recommendations"]) > 5:
            print(f"  ... and {len(results['recommendations']) - 5} more")

    print(f"\n📄 Detailed results saved to: {results_file}")

    return results


if __name__ == "__main__":
    main()
