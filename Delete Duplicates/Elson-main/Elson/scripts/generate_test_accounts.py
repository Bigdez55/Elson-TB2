#!/usr/bin/env python3
"""
Generate test accounts for Elson Wealth Beta Testing

This script creates test user accounts with different profiles for beta testing:
- Standard users
- Guardian users
- Minor users (connected to guardians)
- Admin users

Usage:
    python generate_test_accounts.py [--count N] [--output file.json]
"""

import argparse
import json
import random
import uuid
from datetime import datetime, timedelta

# User role types
ROLES = ["USER", "GUARDIAN", "MINOR", "ADMIN"]
# Risk profiles
RISK_PROFILES = ["LOW", "MODERATE", "AGGRESSIVE"]
# Domain for test emails
EMAIL_DOMAIN = "betatest.elsonwealth.com"
# Default password for all test accounts
DEFAULT_PASSWORD = "BetaTester2025!"

def generate_user(role, user_number):
    """Generate a single user with the specified role"""
    user_id = str(uuid.uuid4())
    first_name = f"{role.capitalize()}{user_number}"
    last_name = "Tester"
    email = f"{role.lower()}{user_number}@{EMAIL_DOMAIN}"
    
    # Set date of birth based on role
    if role == "MINOR":
        # Minors: 13-17 years old
        age = random.randint(13, 17)
    else:
        # Adults: 25-65 years old
        age = random.randint(25, 65)
    
    dob = (datetime.now() - timedelta(days=age*365)).strftime("%Y-%m-%d")
    
    # Set risk profile based on role
    if role == "MINOR":
        risk_profile = "LOW"
    else:
        risk_profile = random.choice(RISK_PROFILES)
    
    # Basic user object
    user = {
        "id": user_id,
        "email": email,
        "password_hash": "$2b$12$AbCdEfGhIjKlMnOpQrStUvWxYzAbCdEfGhIjKlMnOpQrStUv",  # Dummy hash
        "password_plain": DEFAULT_PASSWORD,  # For documentation only, not stored in DB
        "role": role,
        "first_name": first_name,
        "last_name": last_name,
        "date_of_birth": dob,
        "created_at": datetime.now().isoformat(),
        "risk_profile": risk_profile,
        "status": "BETA_TESTER",
        "two_factor_enabled": False
    }
    
    return user

def create_portfolio(user_id, portfolio_number):
    """Create a portfolio for a user"""
    portfolio_id = str(uuid.uuid4())
    portfolio_types = ["STANDARD", "EDUCATION", "RETIREMENT"]
    
    portfolio = {
        "id": portfolio_id,
        "user_id": user_id,
        "name": f"Portfolio {portfolio_number}",
        "description": f"Test portfolio {portfolio_number} for beta testing",
        "created_at": datetime.now().isoformat(),
        "cash_balance": round(random.uniform(1000, 10000), 2),
        "type": random.choice(portfolio_types),
        "guardian_approval": False
    }
    
    return portfolio

def create_relationship(guardian_id, minor_id):
    """Create a guardian-minor relationship"""
    relationship = {
        "id": str(uuid.uuid4()),
        "guardian_id": guardian_id,
        "minor_id": minor_id,
        "relationship_type": "PARENT",
        "created_at": datetime.now().isoformat(),
        "status": "ACTIVE"
    }
    
    return relationship

def main():
    parser = argparse.ArgumentParser(description="Generate test users for Elson Wealth beta testing")
    parser.add_argument("--count", type=int, default=5, help="Number of users per role to generate")
    parser.add_argument("--output", type=str, default="test_accounts.json", help="Output file name")
    args = parser.parse_args()
    
    # Generate users
    users = []
    portfolios = []
    relationships = []
    
    # Generate regular users
    for i in range(1, args.count + 1):
        user = generate_user("USER", i)
        users.append(user)
        
        # Create 1-3 portfolios for each user
        num_portfolios = random.randint(1, 3)
        for j in range(1, num_portfolios + 1):
            portfolio = create_portfolio(user["id"], j)
            portfolios.append(portfolio)
    
    # Generate guardian users
    guardian_ids = []
    for i in range(1, args.count + 1):
        user = generate_user("GUARDIAN", i)
        users.append(user)
        guardian_ids.append(user["id"])
        
        # Create 1-2 portfolios for each guardian
        num_portfolios = random.randint(1, 2)
        for j in range(1, num_portfolios + 1):
            portfolio = create_portfolio(user["id"], j)
            portfolios.append(portfolio)
    
    # Generate minor users (connected to guardians)
    minor_ids = []
    for i in range(1, args.count + 1):
        user = generate_user("MINOR", i)
        users.append(user)
        minor_ids.append(user["id"])
        
        # Create 1 portfolio for each minor
        portfolio = create_portfolio(user["id"], 1)
        portfolio["guardian_approval"] = True
        portfolios.append(portfolio)
    
    # Create relationships between guardians and minors
    # Each guardian can have multiple minors and each minor can have multiple guardians
    for minor_id in minor_ids:
        # Assign 1-2 guardians to each minor
        num_guardians = random.randint(1, min(2, len(guardian_ids)))
        guardian_sample = random.sample(guardian_ids, num_guardians)
        
        for guardian_id in guardian_sample:
            relationship = create_relationship(guardian_id, minor_id)
            relationships.append(relationship)
    
    # Generate 1 admin user
    admin = generate_user("ADMIN", 1)
    users.append(admin)
    
    # Create the output data structure
    output_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "default_password": DEFAULT_PASSWORD,
            "total_users": len(users),
            "total_portfolios": len(portfolios),
            "total_relationships": len(relationships)
        },
        "users": users,
        "portfolios": portfolios,
        "relationships": relationships
    }
    
    # Write to file
    with open(args.output, "w") as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Generated {len(users)} test users with {len(portfolios)} portfolios and {len(relationships)} relationships")
    print(f"Output written to {args.output}")
    print(f"All accounts have the password: {DEFAULT_PASSWORD}")
    
    # Write a summary of test accounts
    with open("test_accounts_summary.md", "w") as f:
        f.write("# Elson Wealth Beta Test Accounts\n\n")
        f.write("## Account Details\n\n")
        f.write("All accounts use the password: `" + DEFAULT_PASSWORD + "`\n\n")
        
        f.write("### Regular Users\n\n")
        f.write("| Email | Name | Password |\n")
        f.write("|-------|------|----------|\n")
        for user in [u for u in users if u["role"] == "USER"]:
            f.write(f"| {user['email']} | {user['first_name']} {user['last_name']} | {DEFAULT_PASSWORD} |\n")
        
        f.write("\n### Guardian Users\n\n")
        f.write("| Email | Name | Password |\n")
        f.write("|-------|------|----------|\n")
        for user in [u for u in users if u["role"] == "GUARDIAN"]:
            f.write(f"| {user['email']} | {user['first_name']} {user['last_name']} | {DEFAULT_PASSWORD} |\n")
        
        f.write("\n### Minor Users\n\n")
        f.write("| Email | Name | Guardians | Password |\n")
        f.write("|-------|------|-----------|----------|\n")
        for user in [u for u in users if u["role"] == "MINOR"]:
            guardian_names = []
            for rel in relationships:
                if rel["minor_id"] == user["id"]:
                    guardian = next((g for g in users if g["id"] == rel["guardian_id"]), None)
                    if guardian:
                        guardian_names.append(f"{guardian['first_name']} {guardian['last_name']}")
            guardians_str = ", ".join(guardian_names)
            f.write(f"| {user['email']} | {user['first_name']} {user['last_name']} | {guardians_str} | {DEFAULT_PASSWORD} |\n")
        
        f.write("\n### Admin Users\n\n")
        f.write("| Email | Name | Password |\n")
        f.write("|-------|------|----------|\n")
        for user in [u for u in users if u["role"] == "ADMIN"]:
            f.write(f"| {user['email']} | {user['first_name']} {user['last_name']} | {DEFAULT_PASSWORD} |\n")
    
    print(f"Summary written to test_accounts_summary.md")

if __name__ == "__main__":
    main()