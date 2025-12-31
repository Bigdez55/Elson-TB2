"""Add portfolio and trade model enhancements from archive

Revision ID: c1b26df926d8
Revises: fe05daf7e673
Create Date: 2025-12-29 08:24:02.545819

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1b26df926d8'
down_revision: Union[str, Sequence[str], None] = 'fe05daf7e673'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLite-compatible migration: Only add columns, skip constraint modifications
    # Add portfolio enhancement columns with defaults
    op.add_column('portfolios', sa.Column('portfolio_type', sa.String(length=20), nullable=True, server_default='standard'))
    op.add_column('portfolios', sa.Column('risk_profile', sa.String(length=20), nullable=True, server_default='moderate'))
    op.add_column('portfolios', sa.Column('max_position_concentration', sa.Float(), nullable=True, server_default='20.0'))
    op.add_column('portfolios', sa.Column('daily_return', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('portfolios', sa.Column('total_return_percent', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('portfolios', sa.Column('available_buying_power', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('portfolios', sa.Column('last_rebalanced_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('portfolios', sa.Column('last_valued_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('portfolios', sa.Column('user_id', sa.Integer(), nullable=True))
    # Note: Foreign keys skipped for SQLite compatibility - handled at application level
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # SQLite-compatible downgrade: Only drop added columns
    op.drop_column('portfolios', 'user_id')
    op.drop_column('portfolios', 'last_valued_at')
    op.drop_column('portfolios', 'last_rebalanced_at')
    op.drop_column('portfolios', 'available_buying_power')
    op.drop_column('portfolios', 'total_return_percent')
    op.drop_column('portfolios', 'daily_return')
    op.drop_column('portfolios', 'max_position_concentration')
    op.drop_column('portfolios', 'risk_profile')
    op.drop_column('portfolios', 'portfolio_type')
    # ### end Alembic commands ###
