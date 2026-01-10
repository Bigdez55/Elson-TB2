#!/usr/bin/env python3
"""
One-time script to update all existing paper trading accounts to $250,000.

This adds $150,000 to all existing portfolios (difference between
new $250,000 initial balance and old $100,000).

Run with: python -m scripts.update_account_balances
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.base import SessionLocal, engine
from app.models.portfolio import Portfolio

# Amount to add to existing accounts
BALANCE_INCREASE = 150000.0


def update_all_accounts():
    """Update all existing portfolio balances."""
    db: Session = SessionLocal()

    try:
        # Get all active portfolios
        portfolios = db.query(Portfolio).filter(Portfolio.is_active == True).all()

        print(f"Found {len(portfolios)} active portfolios to update")

        updated_count = 0
        for portfolio in portfolios:
            old_cash = portfolio.cash_balance
            old_total = portfolio.total_value

            portfolio.cash_balance += BALANCE_INCREASE
            portfolio.total_value += BALANCE_INCREASE

            print(f"  Portfolio {portfolio.id} (User {portfolio.owner_id}): "
                  f"cash ${old_cash:,.2f} -> ${portfolio.cash_balance:,.2f}, "
                  f"total ${old_total:,.2f} -> ${portfolio.total_value:,.2f}")
            updated_count += 1

        db.commit()
        print(f"\nSuccessfully updated {updated_count} portfolios with +${BALANCE_INCREASE:,.0f}")

    except Exception as e:
        db.rollback()
        print(f"Error updating accounts: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Paper Trading Balance Update Script")
    print("Adding $150,000 to all existing accounts")
    print("=" * 60)

    confirm = input("\nThis will update ALL active portfolios. Continue? (yes/no): ")
    if confirm.lower() == "yes":
        update_all_accounts()
    else:
        print("Aborted.")
