"""add_subscription_billing_tables

Revision ID: 7a32be28d1fe
Revises: 1167a82d321b
Create Date: 2025-07-13 23:34:07.130209

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7a32be28d1fe"
down_revision: Union[str, Sequence[str], None] = "1167a82d321b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Subscription table already exists in database, no action needed
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # Subscription table existed before this migration, no action needed
    pass
