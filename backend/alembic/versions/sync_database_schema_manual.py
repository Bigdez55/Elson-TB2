"""Sync database schema with models - Manual Migration

Revision ID: sync_schema_2025_07_14
Revises: 0c1cc482b9b3
Create Date: 2025-07-14 02:45:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "sync_schema_2025_07_14"
down_revision: Union[str, Sequence[str], None] = "0c1cc482b9b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to match models."""
    
    # Helper function to check if column exists
    from sqlalchemy import inspect
    from alembic import context
    
    conn = context.get_bind()
    inspector = inspect(conn)
    
    def column_exists(table_name, column_name):
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    
    def table_exists(table_name):
        return table_name in inspector.get_table_names()
    
    # 1. Add missing columns to users table only if they don't exist
    if not column_exists('users', 'role'):
        op.add_column('users', sa.Column('role', sa.Enum('ADULT', 'MINOR', 'ADMIN', name='userrole'), nullable=False, server_default='ADULT'))
    
    if not column_exists('users', 'birthdate'):
        op.add_column('users', sa.Column('birthdate', sa.String(255), nullable=True))
    
    if not column_exists('users', 'is_superuser'):
        op.add_column('users', sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='0'))
    
    if not column_exists('users', 'two_factor_enabled'):
        op.add_column('users', sa.Column('two_factor_enabled', sa.Boolean(), nullable=False, server_default='0'))
    
    if not column_exists('users', 'failed_login_attempts'):
        op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
    
    if not column_exists('users', 'account_locked_until'):
        op.add_column('users', sa.Column('account_locked_until', sa.DateTime(), nullable=True))
    
    if not column_exists('users', 'password_last_changed'):
        op.add_column('users', sa.Column('password_last_changed', sa.DateTime(), nullable=True))
    
    # 2. Add missing columns to trades table only if they don't exist
    if not column_exists('trades', 'user_id'):
        op.add_column('trades', sa.Column('user_id', sa.Integer(), nullable=True))  # Initially nullable for existing records
    
    if not column_exists('trades', 'investment_amount'):
        op.add_column('trades', sa.Column('investment_amount', sa.Float(), nullable=True))
    
    if not column_exists('trades', 'account_id'):
        op.add_column('trades', sa.Column('account_id', sa.String(255), nullable=True))
    
    if not column_exists('trades', 'is_fractional'):
        op.add_column('trades', sa.Column('is_fractional', sa.Boolean(), nullable=False, server_default='0'))
    
    if not column_exists('trades', 'extended_hours'):
        op.add_column('trades', sa.Column('extended_hours', sa.Boolean(), nullable=False, server_default='0'))
    
    if not column_exists('trades', 'investment_type'):
        op.add_column('trades', sa.Column('investment_type', sa.Enum('STANDARD', 'MICRO', 'ROUNDUP', 'RECURRING', 'DOLLAR_COST_AVERAGE', name='investmenttype'), nullable=False, server_default='STANDARD'))
    
    if not column_exists('trades', 'trade_source'):
        op.add_column('trades', sa.Column('trade_source', sa.Enum('MANUAL', 'MICRO_DEPOSIT', 'ROUNDUP', 'RECURRING', 'AI_RECOMMENDATION', 'REBALANCING', name='tradesource'), nullable=False, server_default='MANUAL'))
    
    if not column_exists('trades', 'trade_metadata'):
        op.add_column('trades', sa.Column('trade_metadata', sa.Text(), nullable=True))
    
    if not column_exists('trades', 'total_amount'):
        op.add_column('trades', sa.Column('total_amount', sa.Float(), nullable=True))
    
    # 3. Make quantity nullable in trades table (for dollar-based orders)
    # SQLite doesn't support ALTER COLUMN, so we'll handle this with batch operations
    with op.batch_alter_table('trades') as batch_op:
        batch_op.alter_column('quantity', nullable=True)
    
    # 4. Update TradeStatus enum to include new values
    # First, add the new enum values to the existing enums
    op.execute("UPDATE trades SET status = 'CANCELED' WHERE status = 'CANCELLED'")  # Normalize existing data
    
    # 5. Create new tables only if they don't exist
    
    # Create accounts table (referenced in trade model)
    if not table_exists('accounts'):
        op.create_table('accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('guardian_id', sa.Integer(), nullable=True),
        sa.Column('account_number', sa.String(255), nullable=False),
        sa.Column('account_type', sa.Enum('INDIVIDUAL', 'CUSTODIAL', 'JOINT', name='accounttype'), nullable=False),
        sa.Column('broker', sa.String(100), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'PENDING', 'CLOSED', name='accountstatus'), nullable=False),
        sa.Column('balance', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('buying_power', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('is_paper_account', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['guardian_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
        op.create_index(op.f('ix_accounts_account_number'), 'accounts', ['account_number'], unique=True)
        op.create_index(op.f('ix_accounts_id'), 'accounts', ['id'], unique=False)
    
    # Create subscriptions table
    if not table_exists('subscriptions'):
        op.create_table('subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('plan', sa.Enum('FREE', 'PREMIUM', 'FAMILY', name='subscriptionplan'), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'CANCELED', 'PAST_DUE', name='subscriptionstatus'), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('billing_cycle', sa.Enum('MONTHLY', 'YEARLY', name='billingcycle'), nullable=False),
        sa.Column('current_period_start', sa.DateTime(), nullable=False),
        sa.Column('current_period_end', sa.DateTime(), nullable=False),
        sa.Column('trial_start', sa.DateTime(), nullable=True),
        sa.Column('trial_end', sa.DateTime(), nullable=True),
        sa.Column('provider_subscription_id', sa.String(), nullable=True),
        sa.Column('provider_customer_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
        op.create_index(op.f('ix_subscriptions_id'), 'subscriptions', ['id'], unique=False)
    
    # Create notifications table
    if not table_exists('notifications'):
        op.create_table('notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('type', sa.Enum('INFO', 'WARNING', 'ERROR', 'SUCCESS', 'TRADE_EXECUTION', 'MARKET_ALERT', 'ACCOUNT_UPDATE', name='notificationtype'), nullable=False),
        sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'URGENT', name='notificationpriority'), nullable=False, server_default='MEDIUM'),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('action_url', sa.String(500), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
        op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
    
    # Create roundup_transactions table
    if not table_exists('roundup_transactions'):
        op.create_table('roundup_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('transaction_amount', sa.Float(), nullable=False),
        sa.Column('roundup_amount', sa.Float(), nullable=False),
        sa.Column('transaction_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('status', sa.String(50), nullable=True, server_default='pending'),
        sa.Column('invested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trade_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['trade_id'], ['trades.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
        op.create_index(op.f('ix_roundup_transactions_id'), 'roundup_transactions', ['id'], unique=False)
    
    # Create recurring_investments table
    if not table_exists('recurring_investments'):
        op.create_table('recurring_investments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('frequency', sa.Enum('WEEKLY', 'BIWEEKLY', 'MONTHLY', name='investmentfrequency'), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=True),
        sa.Column('day_of_month', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('next_execution', sa.DateTime(), nullable=False),
        sa.Column('last_execution', sa.DateTime(), nullable=True),
        sa.Column('total_invested', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('execution_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
        op.create_index(op.f('ix_recurring_investments_id'), 'recurring_investments', ['id'], unique=False)
    
    # 6. Fix foreign key type mismatch in trade_executions (if needed)
    # Check if the trade_id column needs type conversion
    try:
        trade_exec_columns = inspector.get_columns('trade_executions')
        trade_id_col = next((col for col in trade_exec_columns if col['name'] == 'trade_id'), None)
        
        if trade_id_col and str(trade_id_col['type']).upper().startswith('INTEGER'):
            # Need to fix the type mismatch
            with op.batch_alter_table('trade_executions') as batch_op:
                try:
                    batch_op.drop_constraint('trade_executions_trade_id_fkey', type_='foreignkey')
                except Exception:
                    pass  # Constraint may not exist
                batch_op.alter_column('trade_id', existing_type=sa.INTEGER(), type_=sa.String(36))
                batch_op.create_foreign_key('trade_executions_trade_id_fkey', 'trades', ['trade_id'], ['id'])
    except Exception as e:
        print(f"Could not fix trade_executions type mismatch: {e}")
    
    # 7. Add foreign key constraint for user_id in trades table (if it doesn't exist)
    try:
        # Check if foreign key already exists
        foreign_keys = inspector.get_foreign_keys('trades')
        user_fk_exists = any(fk for fk in foreign_keys if 'user_id' in fk.get('constrained_columns', []))
        
        if not user_fk_exists and column_exists('trades', 'user_id'):
            op.create_foreign_key('trades_user_id_fkey', 'trades', 'users', ['user_id'], ['id'])
    except Exception as e:
        print(f"Could not add user_id foreign key: {e}")


def downgrade() -> None:
    """Downgrade schema."""
    
    # Drop foreign key constraints
    op.drop_constraint('trades_user_id_fkey', 'trades', type_='foreignkey')
    
    # Fix trade_executions back to INTEGER
    with op.batch_alter_table('trade_executions') as batch_op:
        batch_op.drop_constraint('trade_executions_trade_id_fkey', type_='foreignkey')
        batch_op.alter_column('trade_id', existing_type=sa.String(36), type_=sa.INTEGER())
        batch_op.create_foreign_key('trade_executions_trade_id_fkey', 'trades', ['trade_id'], ['id'])
    
    # Drop new tables
    op.drop_index(op.f('ix_recurring_investments_id'), table_name='recurring_investments')
    op.drop_table('recurring_investments')
    
    op.drop_index(op.f('ix_roundup_transactions_id'), table_name='roundup_transactions')
    op.drop_table('roundup_transactions')
    
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_table('notifications')
    
    op.drop_index(op.f('ix_subscriptions_id'), table_name='subscriptions')
    op.drop_table('subscriptions')
    
    op.drop_index(op.f('ix_accounts_account_number'), table_name='accounts')
    op.drop_index(op.f('ix_accounts_id'), table_name='accounts')
    op.drop_table('accounts')
    
    # Remove columns from trades table
    op.drop_column('trades', 'total_amount')
    op.drop_column('trades', 'trade_metadata')
    op.drop_column('trades', 'trade_source')
    op.drop_column('trades', 'investment_type')
    op.drop_column('trades', 'extended_hours')
    op.drop_column('trades', 'is_fractional')
    op.drop_column('trades', 'account_id')
    op.drop_column('trades', 'investment_amount')
    op.drop_column('trades', 'user_id')
    
    # Make quantity non-nullable again
    with op.batch_alter_table('trades') as batch_op:
        batch_op.alter_column('quantity', nullable=False)
    
    # Remove columns from users table
    op.drop_column('users', 'password_last_changed')
    op.drop_column('users', 'account_locked_until')
    op.drop_column('users', 'failed_login_attempts')
    op.drop_column('users', 'two_factor_enabled')
    op.drop_column('users', 'is_superuser')
    op.drop_column('users', 'birthdate')
    op.drop_column('users', 'role')