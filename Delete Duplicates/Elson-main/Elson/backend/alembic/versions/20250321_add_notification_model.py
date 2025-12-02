"""add_notification_model

Revision ID: 20250321_add_notification_model
Revises: 20250320_add_metadata_to_recurring_investments
Create Date: 2025-03-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
import json

# revision identifiers, used by Alembic.
revision: str = '20250321_add_notification_model'
down_revision: Union[str, None] = '20250320_add_metadata_to_recurring_investments'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_connection_dialect():
    """Determine if we're using SQLite or PostgreSQL"""
    conn = op.get_bind()
    inspector = inspect(conn)
    return inspector.dialect.name


def upgrade() -> None:
    dialect = get_connection_dialect()
    
    if dialect == 'postgresql':
        # PostgreSQL implementation
        from sqlalchemy.dialects.postgresql import JSONB
        
        # Create notification_types enum
        op.execute("""
        CREATE TYPE notification_type AS ENUM (
            'trade_request', 'trade_executed', 'withdrawal', 'deposit', 'login', 
            'settings_change', 'request', 'trade_approved', 'trade_rejected', 
            'new_recommendation', 'portfolio_rebalance', 'account_linked', 'security_alert'
        )
        """)
        
        # Create notifications table with PostgreSQL JSONB
        op.create_table(
            'notifications',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('type', sa.String(), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('requires_action', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('data', JSONB, nullable=True),
            sa.Column('minor_account_id', sa.Integer(), nullable=True),
            sa.Column('trade_id', sa.Integer(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['minor_account_id'], ['accounts.id'], ),
            sa.ForeignKeyConstraint(['trade_id'], ['trades.id'], )
        )
    else:
        # SQLite implementation
        # Create notifications table with TEXT for JSON data
        op.create_table(
            'notifications',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('type', sa.String(), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('requires_action', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('is_read', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('timestamp', sa.DateTime(), nullable=False),
            sa.Column('data', sa.Text(), nullable=True),  # SQLite doesn't support JSONB, use TEXT
            sa.Column('minor_account_id', sa.Integer(), nullable=True),
            sa.Column('trade_id', sa.Integer(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['minor_account_id'], ['accounts.id'], ),
            sa.ForeignKeyConstraint(['trade_id'], ['trades.id'], )
        )
    
    # Create index on user_id for faster lookups
    op.create_index(
        op.f('ix_notifications_user_id'),
        'notifications',
        ['user_id'],
        unique=False
    )
    
    # Create index on timestamp for faster sorting
    op.create_index(
        op.f('ix_notifications_timestamp'),
        'notifications',
        ['timestamp'],
        unique=False
    )
    
    # Create index on is_read for filtering
    op.create_index(
        op.f('ix_notifications_is_read'),
        'notifications',
        ['is_read'],
        unique=False
    )


def downgrade() -> None:
    # Drop the notifications table
    op.drop_index(op.f('ix_notifications_is_read'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_timestamp'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_table('notifications')
    
    dialect = get_connection_dialect()
    if dialect == 'postgresql':
        # Drop the notification_type enum
        op.execute("DROP TYPE notification_type")