"""add executed_by field to trades

Revision ID: 20250305_add_executed_by_field
Revises: 20250305_add_recurring_investments
Create Date: 2025-03-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250305_add_executed_by_field'
down_revision: str = '20250305_add_recurring_investments'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add executed_by column to trades table
    op.add_column('trades', sa.Column('executed_by', sa.String(20), nullable=True))


def downgrade() -> None:
    # Remove executed_by column from trades table
    op.drop_column('trades', 'executed_by')