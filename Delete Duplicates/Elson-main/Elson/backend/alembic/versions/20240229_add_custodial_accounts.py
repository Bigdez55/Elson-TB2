"""add_custodial_accounts

Revision ID: 20240229_add_custodial_accounts
Revises: 20240110_initial_migration
Create Date: 2024-02-29 12:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20240229_add_custodial_accounts'
down_revision = '20240110_initial_migration'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types
    op.execute("CREATE TYPE user_role AS ENUM ('adult', 'minor', 'admin');")
    op.execute("CREATE TYPE account_type AS ENUM ('personal', 'custodial');")
    op.execute("CREATE TYPE trade_status AS ENUM ('pending_approval', 'pending', 'filled', 'cancelled', 'rejected', 'expired');")
    op.execute("CREATE TYPE order_type AS ENUM ('market', 'limit', 'stop', 'stop_limit');")
    
    # Add role and birthdate columns to users table
    op.add_column('users', sa.Column('role', sa.Enum('adult', 'minor', 'admin', name='user_role'), nullable=False, server_default='adult'))
    op.add_column('users', sa.Column('birthdate', sa.Date(), nullable=True))
    
    # Create accounts table
    op.create_table('accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('guardian_id', sa.Integer(), nullable=True),
        sa.Column('account_type', sa.Enum('personal', 'custodial', name='account_type'), nullable=False, server_default='personal'),
        sa.Column('account_number', sa.String(), nullable=False),
        sa.Column('institution', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['guardian_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('account_number')
    )
    op.create_index(op.f('ix_accounts_account_number'), 'accounts', ['account_number'], unique=True)
    
    # Update portfolios table
    op.add_column('portfolios', sa.Column('account_id', sa.Integer(), nullable=True))
    op.add_column('portfolios', sa.Column('risk_profile', sa.String(), nullable=True, server_default='moderate'))
    op.add_column('portfolios', sa.Column('last_rebalanced_at', sa.DateTime(), nullable=True))
    op.create_foreign_key('fk_portfolio_account', 'portfolios', 'accounts', ['account_id'], ['id'])
    op.drop_constraint('portfolios_user_id_key', 'portfolios', type_='unique')  # Allow multiple portfolios per user
    
    # Update trades table
    op.add_column('trades', sa.Column('status', sa.Enum('pending_approval', 'pending', 'filled', 'cancelled', 'rejected', 'expired', name='trade_status'), 
                                  nullable=False, server_default='pending'))
    op.add_column('trades', sa.Column('order_type', sa.Enum('market', 'limit', 'stop', 'stop_limit', name='order_type'), 
                                   nullable=False, server_default='market'))
    op.add_column('trades', sa.Column('requested_by_user_id', sa.Integer(), nullable=True))
    op.add_column('trades', sa.Column('approved_by_user_id', sa.Integer(), nullable=True))
    op.add_column('trades', sa.Column('rejection_reason', sa.Text(), nullable=True))
    op.add_column('trades', sa.Column('approved_at', sa.DateTime(), nullable=True))
    op.add_column('trades', sa.Column('executed_at', sa.DateTime(), nullable=True))
    op.create_foreign_key('fk_trade_requested_by', 'trades', 'users', ['requested_by_user_id'], ['id'])
    op.create_foreign_key('fk_trade_approved_by', 'trades', 'users', ['approved_by_user_id'], ['id'])


def downgrade():
    # Drop foreign keys
    op.drop_constraint('fk_trade_approved_by', 'trades', type_='foreignkey')
    op.drop_constraint('fk_trade_requested_by', 'trades', type_='foreignkey')
    op.drop_constraint('fk_portfolio_account', 'portfolios', type_='foreignkey')
    
    # Drop columns from trades table
    op.drop_column('trades', 'executed_at')
    op.drop_column('trades', 'approved_at')
    op.drop_column('trades', 'rejection_reason')
    op.drop_column('trades', 'approved_by_user_id')
    op.drop_column('trades', 'requested_by_user_id')
    op.drop_column('trades', 'order_type')
    op.drop_column('trades', 'status')
    
    # Drop columns from portfolios table
    op.add_constraint('portfolios_user_id_key', 'portfolios', ['user_id'], type_='unique')
    op.drop_column('portfolios', 'last_rebalanced_at')
    op.drop_column('portfolios', 'risk_profile')
    op.drop_column('portfolios', 'account_id')
    
    # Drop accounts table
    op.drop_index(op.f('ix_accounts_account_number'), table_name='accounts')
    op.drop_table('accounts')
    
    # Drop columns from users table
    op.drop_column('users', 'birthdate')
    op.drop_column('users', 'role')
    
    # Drop enum types
    op.execute("DROP TYPE order_type;")
    op.execute("DROP TYPE trade_status;") 
    op.execute("DROP TYPE account_type;")
    op.execute("DROP TYPE user_role;")