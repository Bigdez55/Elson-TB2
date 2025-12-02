"""Initial migration

Revision ID: 20240110_initial_migration
Revises: 
Create Date: 2024-01-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20240110_initial_migration'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_superuser', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )

    # Create portfolios table
    op.create_table(
        'portfolios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('total_value', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('cash_balance', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('invested_amount', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('positions', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # Create positions table
    op.create_table(
        'positions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('portfolio_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(10), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('average_price', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('current_price', sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create trades table
    op.create_table(
        'trades',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(10), nullable=False),
        sa.Column('order_type', sa.String(), nullable=False),
        sa.Column('side', sa.String(), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('price', sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column('limit_price', sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column('stop_price', sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('filled_at', sa.DateTime(), nullable=True),
        sa.Column('commission', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column('external_order_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_trades_symbol', 'trades', ['symbol'])
    op.create_index('ix_trades_created_at', 'trades', ['created_at'])
    op.create_index('ix_positions_symbol', 'positions', ['symbol'])
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_username', 'users', ['username'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('trades')
    op.drop_table('positions')
    op.drop_table('portfolios')
    op.drop_table('users')