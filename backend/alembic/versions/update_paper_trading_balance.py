"""Update existing paper trading accounts to $250,000

This migration adds $150,000 to all existing portfolios to reflect
the new paper trading initial balance of $250,000 (up from $100,000).

Revision ID: update_paper_balance
Revises:
Create Date: 2026-01-10

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'update_paper_balance'
down_revision = None
branch_labels = None
depends_on = None

# Amount to add to existing accounts (difference between new and old initial balance)
BALANCE_INCREASE = 150000.0


def upgrade():
    """Add $150,000 to all existing portfolio cash balances and total values."""
    # Use raw SQL for the update to handle it in a single transaction
    op.execute(
        f"""
        UPDATE portfolios
        SET cash_balance = cash_balance + {BALANCE_INCREASE},
            total_value = total_value + {BALANCE_INCREASE}
        WHERE is_active = true
        """
    )


def downgrade():
    """Remove the $150,000 that was added (revert to original balances)."""
    op.execute(
        f"""
        UPDATE portfolios
        SET cash_balance = cash_balance - {BALANCE_INCREASE},
            total_value = total_value - {BALANCE_INCREASE}
        WHERE is_active = true
        """
    )
