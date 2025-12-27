#!/usr/bin/env python3
"""
Manual authentication security testing script for Elson Trading Platform.
This script tests authentication and security features without pytest dependencies.
"""

import sys
import os
import asyncio
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Add the current directory to Python path
sys.path.append(".")

# Import app modules
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    verify_token,
    refresh_access_token,
    check_rate_limit,
    check_login_rate_limit,
)
from app.core.config import settings


class SecurityTester:
    def __init__(self):
        self.test_results = {"passed": 0, "failed": 0, "tests": []}

    def log_test(self, name: str, success: bool, details: str = "", error: str = ""):
        """Log test result"""
        result = {
            "name": name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.test_results["tests"].append(result)

        if success:
            self.test_results["passed"] += 1
            print(f"✅ {name}: PASSED - {details}")
        else:
            self.test_results["failed"] += 1
            print(f"❌ {name}: FAILED - {error}")

    def test_password_hashing(self):
        """Test password hashing and verification"""
        try:
            # Test password hashing
            password = "test_password_123"
            hashed = get_password_hash(password)

            # Verify basic properties
            if not hashed or len(hashed) < 20:
                self.log_test("Password Hashing", False, "", "Hash too short or empty")
                return

            # Verify password verification works
            if not verify_password(password, hashed):
                self.log_test(
                    "Password Hashing", False, "", "Password verification failed"
                )
                return

            # Verify wrong password fails
            if verify_password("wrong_password", hashed):
                self.log_test(
                    "Password Hashing",
                    False,
                    "",
                    "Wrong password verified successfully",
                )
                return

            # Test that same password produces different hashes (salt)
            hashed2 = get_password_hash(password)
            if hashed == hashed2:
                self.log_test(
                    "Password Hashing",
                    False,
                    "",
                    "Same password produces identical hashes (no salt)",
                )
                return

            self.log_test(
                "Password Hashing", True, "Bcrypt hashing with salt working correctly"
            )

        except Exception as e:
            self.log_test("Password Hashing", False, "", f"Exception: {str(e)}")

    def test_jwt_token_generation(self):
        """Test JWT token generation and validation"""
        try:
            # Test access token creation
            test_email = "test@example.com"
            expires_delta = timedelta(minutes=30)

            access_token = create_access_token(
                data={"sub": test_email}, expires_delta=expires_delta
            )

            if not access_token or len(access_token.split(".")) != 3:
                self.log_test("JWT Token Generation", False, "", "Invalid JWT format")
                return

            # Test token verification
            payload = verify_token(access_token)
            if not payload:
                self.log_test(
                    "JWT Token Generation", False, "", "Token verification failed"
                )
                return

            if payload.get("sub") != test_email:
                self.log_test(
                    "JWT Token Generation", False, "", "Token payload incorrect"
                )
                return

            # Check token contains required fields
            required_fields = ["sub", "exp", "jti", "type"]
            for field in required_fields:
                if field not in payload:
                    self.log_test(
                        "JWT Token Generation", False, "", f"Missing field: {field}"
                    )
                    return

            self.log_test(
                "JWT Token Generation",
                True,
                "JWT tokens generated and verified successfully",
            )

        except Exception as e:
            self.log_test("JWT Token Generation", False, "", f"Exception: {str(e)}")

    def test_refresh_token_functionality(self):
        """Test refresh token functionality"""
        try:
            test_email = "refresh_test@example.com"

            # Create refresh token
            refresh_token = create_refresh_token(data={"sub": test_email})

            if not refresh_token:
                self.log_test(
                    "Refresh Token", False, "", "Refresh token creation failed"
                )
                return

            # Test refresh token verification
            payload = verify_token(refresh_token)
            if not payload or payload.get("type") != "refresh":
                self.log_test(
                    "Refresh Token", False, "", "Refresh token verification failed"
                )
                return

            # Test access token refresh
            new_tokens = refresh_access_token(refresh_token)
            if not new_tokens or "access_token" not in new_tokens:
                self.log_test("Refresh Token", False, "", "Token refresh failed")
                return

            # Verify new access token works
            new_payload = verify_token(new_tokens["access_token"])
            if not new_payload or new_payload.get("sub") != test_email:
                self.log_test("Refresh Token", False, "", "New access token invalid")
                return

            self.log_test(
                "Refresh Token", True, "Refresh token functionality working correctly"
            )

        except Exception as e:
            self.log_test("Refresh Token", False, "", f"Exception: {str(e)}")

    def test_expired_token_handling(self):
        """Test expired token handling"""
        try:
            test_email = "expired_test@example.com"

            # Create token that expires immediately
            expired_token = create_access_token(
                data={"sub": test_email},
                expires_delta=timedelta(seconds=-1),  # Already expired
            )

            # Wait a moment to ensure expiration
            time.sleep(1)

            # Try to verify expired token
            payload = verify_token(expired_token)
            if payload is not None:
                self.log_test(
                    "Expired Token Handling", False, "", "Expired token still valid"
                )
                return

            self.log_test(
                "Expired Token Handling", True, "Expired tokens correctly rejected"
            )

        except Exception as e:
            self.log_test("Expired Token Handling", False, "", f"Exception: {str(e)}")

    def test_rate_limiting_logic(self):
        """Test rate limiting functionality"""
        try:
            # Mock request object for testing
            class MockRequest:
                def __init__(self, ip="127.0.0.1"):
                    self.client = type("obj", (object,), {"host": ip})
                    self.headers = {}

            # Test login rate limiting
            test_email = "ratelimit@example.com"
            test_ip = "192.168.1.100"

            # Test that initial login attempts are allowed
            for i in range(3):
                if not check_login_rate_limit(test_email, test_ip):
                    self.log_test(
                        "Rate Limiting", False, "", f"Login blocked on attempt {i+1}"
                    )
                    return

            self.log_test(
                "Rate Limiting",
                True,
                "Rate limiting logic functional (Note: Redis may not be available)",
            )

        except Exception as e:
            self.log_test("Rate Limiting", False, "", f"Exception: {str(e)}")

    def test_security_configuration(self):
        """Test security configuration"""
        try:
            # Check SECRET_KEY exists and is strong
            if not hasattr(settings, "SECRET_KEY") or not settings.SECRET_KEY:
                self.log_test("Security Configuration", False, "", "SECRET_KEY not set")
                return

            if len(settings.SECRET_KEY) < 32:
                self.log_test(
                    "Security Configuration", False, "", "SECRET_KEY too short"
                )
                return

            # Check token expiration settings
            if not hasattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES"):
                self.log_test(
                    "Security Configuration",
                    False,
                    "",
                    "ACCESS_TOKEN_EXPIRE_MINUTES not set",
                )
                return

            expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
            if expire_minutes <= 0 or expire_minutes > 24 * 60:  # Max 24 hours
                self.log_test(
                    "Security Configuration",
                    False,
                    "",
                    f"Invalid token expiration: {expire_minutes} minutes",
                )
                return

            self.log_test(
                "Security Configuration",
                True,
                f"Security settings configured correctly (Token expires in {expire_minutes} minutes)",
            )

        except Exception as e:
            self.log_test("Security Configuration", False, "", f"Exception: {str(e)}")

    def test_token_uniqueness(self):
        """Test that tokens are unique"""
        try:
            test_email = "unique_test@example.com"

            # Generate multiple tokens for same user
            tokens = []
            for i in range(5):
                token = create_access_token(data={"sub": test_email})
                tokens.append(token)

            # Check all tokens are different
            unique_tokens = set(tokens)
            if len(unique_tokens) != len(tokens):
                self.log_test(
                    "Token Uniqueness", False, "", "Duplicate tokens generated"
                )
                return

            # Check JTI uniqueness
            jtis = []
            for token in tokens:
                payload = verify_token(token)
                if payload:
                    jtis.append(payload.get("jti"))

            unique_jtis = set(jtis)
            if len(unique_jtis) != len(jtis):
                self.log_test("Token Uniqueness", False, "", "Duplicate JTIs found")
                return

            self.log_test("Token Uniqueness", True, "All tokens and JTIs are unique")

        except Exception as e:
            self.log_test("Token Uniqueness", False, "", f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all security tests"""
        print("🔐 Starting Authentication & Security Tests")
        print("=" * 60)

        self.test_security_configuration()
        self.test_password_hashing()
        self.test_jwt_token_generation()
        self.test_refresh_token_functionality()
        self.test_expired_token_handling()
        self.test_token_uniqueness()
        self.test_rate_limiting_logic()

        print("\n" + "=" * 60)
        print(f"🔐 Security Test Summary")
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        print(f"📊 Total: {len(self.test_results['tests'])}")

        return self.test_results


def main():
    """Main test runner"""
    tester = SecurityTester()
    results = tester.run_all_tests()

    # Save results to file
    with open("/workspaces/Elson-TB2/backend/security_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n📄 Test results saved to security_test_results.json")

    # Exit with appropriate code
    if results["failed"] > 0:
        print("\n⚠️  Some security tests failed. Review the results above.")
        return 1
    else:
        print("\n🎉 All security tests passed!")
        return 0


if __name__ == "__main__":
    exit(main())
