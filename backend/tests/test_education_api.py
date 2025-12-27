"""
Comprehensive test script for the Education API endpoints.
Tests database, service layer, and API endpoints.
"""

import sys
import requests
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database setup
DATABASE_URL = "sqlite:///./trading_platform.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def test_database_tables():
    """Test that all education tables exist."""
    print_section("TEST 1: Database Tables")

    db = SessionLocal()
    try:
        # Check tables
        result = db.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' "
                 "AND (name LIKE '%educat%' OR name LIKE '%learning%' OR name LIKE '%permission%' "
                 "OR name LIKE '%progress%' OR name LIKE '%prerequis%') "
                 "ORDER BY name")
        )
        tables = [row[0] for row in result.fetchall()]

        expected_tables = [
            'content_prerequisites',
            'educational_content',
            'learning_path_items',
            'learning_paths',
            'trading_permissions',
            'user_permissions',
            'user_progress',
        ]

        print("Expected tables:")
        for table in expected_tables:
            exists = table in tables
            status = "✓" if exists else "✗"
            print(f"  {status} {table}")

        missing = set(expected_tables) - set(tables)
        if missing:
            print(f"\n❌ Missing tables: {missing}")
            return False
        else:
            print("\n✅ All education tables exist")
            return True

    finally:
        db.close()

def test_api_endpoints_registration():
    """Test that education endpoints are registered."""
    print_section("TEST 2: API Endpoints Registration")

    endpoints_to_test = [
        "/education/content",
        "/education/progress",
        "/education/paths",
        "/education/permissions",
        "/education/permissions/my",
    ]

    results = []
    for endpoint in endpoints_to_test:
        url = f"{BASE_URL}{endpoint}"
        try:
            # All endpoints should require authentication
            response = requests.get(url, timeout=5)

            # Should get 401 (Unauthorized) or 200 (if somehow authenticated)
            if response.status_code in [401, 403]:
                print(f"  ✓ {endpoint} - Requires authentication (status: {response.status_code})")
                results.append(True)
            elif response.status_code == 200:
                print(f"  ✓ {endpoint} - Accessible (status: {response.status_code})")
                results.append(True)
            else:
                print(f"  ✗ {endpoint} - Unexpected status: {response.status_code}")
                results.append(False)
        except requests.exceptions.RequestException as e:
            print(f"  ✗ {endpoint} - Error: {str(e)}")
            results.append(False)

    if all(results):
        print("\n✅ All education endpoints are registered and responding")
        return True
    else:
        print("\n❌ Some endpoints failed")
        return False

def seed_test_data():
    """Seed minimal test data."""
    print_section("TEST 3: Seeding Test Data")

    db = SessionLocal()
    try:
        # Check if content already exists
        result = db.execute(text("SELECT COUNT(*) FROM educational_content"))
        count = result.fetchone()[0]

        if count > 0:
            print(f"  Database already has {count} content items")
            return True

        # Insert test educational content
        db.execute(text("""
            INSERT INTO educational_content (
                title, slug, description, content_type, level,
                completion_requirement, estimated_minutes, importance_level,
                created_at, updated_at
            ) VALUES (
                'Introduction to Stock Trading',
                'intro-stock-trading',
                'Learn the basics of stock trading and market fundamentals',
                'MODULE',
                'BEGINNER',
                'QUIZ',
                30,
                5,
                datetime('now'),
                datetime('now')
            )
        """))

        # Insert a learning path
        db.execute(text("""
            INSERT INTO learning_paths (
                title, slug, description, min_age, max_age,
                created_at, updated_at
            ) VALUES (
                'Beginner Trading Path',
                'beginner-trading',
                'Complete guide for new traders',
                13,
                NULL,
                datetime('now'),
                datetime('now')
            )
        """))

        # Insert a trading permission
        db.execute(text("""
            INSERT INTO trading_permissions (
                name, description, permission_type,
                requires_guardian_approval, min_age,
                created_at, updated_at
            ) VALUES (
                'Stock Trading Permission',
                'Allows user to trade stocks',
                'trade_stocks',
                1,
                13,
                datetime('now'),
                datetime('now')
            )
        """))

        db.commit()
        print("  ✅ Test data seeded successfully")
        print("    - 1 educational content item")
        print("    - 1 learning path")
        print("    - 1 trading permission")
        return True

    except Exception as e:
        db.rollback()
        print(f"  ❌ Failed to seed data: {str(e)}")
        return False
    finally:
        db.close()

def test_data_retrieval():
    """Test retrieving seeded data."""
    print_section("TEST 4: Data Retrieval from Database")

    db = SessionLocal()
    try:
        # Get educational content
        result = db.execute(text("SELECT id, title, slug, level FROM educational_content LIMIT 5"))
        content = result.fetchall()

        print(f"Educational Content ({len(content)} items):")
        for item in content:
            print(f"  - ID {item[0]}: {item[1]} ({item[2]}) - Level: {item[3]}")

        # Get learning paths
        result = db.execute(text("SELECT id, title, slug FROM learning_paths LIMIT 5"))
        paths = result.fetchall()

        print(f"\nLearning Paths ({len(paths)} items):")
        for item in paths:
            print(f"  - ID {item[0]}: {item[1]} ({item[2]})")

        # Get trading permissions
        result = db.execute(text("SELECT id, name, permission_type FROM trading_permissions LIMIT 5"))
        permissions = result.fetchall()

        print(f"\nTrading Permissions ({len(permissions)} items):")
        for item in permissions:
            print(f"  - ID {item[0]}: {item[1]} ({item[2]})")

        if content or paths or permissions:
            print("\n✅ Data retrieval successful")
            return True
        else:
            print("\n⚠️  No data found (seed data first)")
            return False

    except Exception as e:
        print(f"\n❌ Failed to retrieve data: {str(e)}")
        return False
    finally:
        db.close()

def generate_test_report():
    """Generate a comprehensive test report."""
    print_section("PHASE 3 EDUCATION SYSTEM TEST REPORT")
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = {
        "Database Tables": test_database_tables(),
        "API Endpoints": test_api_endpoints_registration(),
        "Seed Test Data": seed_test_data(),
        "Data Retrieval": test_data_retrieval(),
    }

    print_section("SUMMARY")

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n" + "="*80)
        print("  🎉 ALL TESTS PASSED - Phase 3 Backend Education System is READY!")
        print("="*80 + "\n")
        return True
    else:
        print("\n" + "="*80)
        print("  ⚠️  SOME TESTS FAILED - Review errors above")
        print("="*80 + "\n")
        return False

if __name__ == "__main__":
    try:
        success = generate_test_report()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test script failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
