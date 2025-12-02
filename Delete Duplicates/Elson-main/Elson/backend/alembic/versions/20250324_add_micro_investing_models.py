"""Add micro-investing models

Revision ID: 20250324_add_micro_investing_models
Revises: 20250321_add_notification_model
Create Date: 2025-03-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250324_add_micro_investing_models'
down_revision = '20250321_add_notification_model'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types
    investment_type = sa.Enum('standard', 'dollar_based', 'micro', 'roundup', name='investmenttype')
    investment_type.create(op.get_bind())
    
    trade_source = sa.Enum('user_initiated', 'recurring', 'roundup', 'auto_invest', 'micro_deposit', name='tradesource')
    trade_source.create(op.get_bind())
    
    order_type = sa.Enum('market', 'limit', name='ordertype')
    order_type.create(op.get_bind())
    
    roundup_frequency = sa.Enum('daily', 'weekly', 'threshold', name='roundupfrequency')
    roundup_frequency.create(op.get_bind())
    
    micro_invest_target = sa.Enum('default_portfolio', 'specific_portfolio', 'specific_symbol', 'recommended_etf', name='microinvesttarget')
    micro_invest_target.create(op.get_bind())
    
    # Add new status to existing trade_status enum
    op.execute("ALTER TYPE tradestatus ADD VALUE IF NOT EXISTS 'pending_approval'")
    
    # Add columns to trades table
    op.add_column('trades', sa.Column('is_fractional', sa.Boolean(), nullable=True))
    op.add_column('trades', sa.Column('investment_amount', sa.Float(), nullable=True))
    op.add_column('trades', sa.Column('investment_type', sa.Enum('standard', 'dollar_based', 'micro', 'roundup', name='investmenttype'), nullable=True))
    op.add_column('trades', sa.Column('order_type', sa.Enum('market', 'limit', name='ordertype'), nullable=True))
    op.add_column('trades', sa.Column('trade_source', sa.Enum('user_initiated', 'recurring', 'roundup', 'auto_invest', 'micro_deposit', name='tradesource'), nullable=True))
    op.add_column('trades', sa.Column('total_amount', sa.Float(), nullable=True))
    op.add_column('trades', sa.Column('filled_quantity', sa.Float(), nullable=True))
    op.add_column('trades', sa.Column('filled_price', sa.Float(), nullable=True))
    op.add_column('trades', sa.Column('recurring_investment_id', sa.Integer(), nullable=True))
    op.add_column('trades', sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.create_foreign_key('fk_trades_recurring_investment', 'trades', 'recurring_investments', ['recurring_investment_id'], ['id'])
    
    # Make quantity nullable
    op.alter_column('trades', 'quantity', existing_type=sa.Float(), nullable=True)
    
    # Create roundup_transactions table
    op.create_table('roundup_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('transaction_amount', sa.Float(), nullable=False),
        sa.Column('roundup_amount', sa.Float(), nullable=False),
        sa.Column('transaction_date', sa.DateTime(), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('invested_at', sa.DateTime(), nullable=True),
        sa.Column('trade_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['trade_id'], ['trades.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_roundup_transactions_id'), 'roundup_transactions', ['id'], unique=False)
    
    # Create user_settings table
    op.create_table('user_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('micro_investing_enabled', sa.Boolean(), nullable=True),
        sa.Column('roundup_enabled', sa.Boolean(), nullable=True),
        sa.Column('roundup_multiplier', sa.Float(), nullable=True),
        sa.Column('roundup_frequency', roundup_frequency, nullable=True),
        sa.Column('roundup_threshold', sa.Float(), nullable=True),
        sa.Column('micro_invest_target_type', micro_invest_target, nullable=True),
        sa.Column('micro_invest_portfolio_id', sa.Integer(), nullable=True),
        sa.Column('micro_invest_symbol', sa.String(length=10), nullable=True),
        sa.Column('bank_account_linked', sa.Boolean(), nullable=True),
        sa.Column('card_accounts_linked', sa.Boolean(), nullable=True),
        sa.Column('linked_accounts_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('notify_on_roundup', sa.Boolean(), nullable=True),
        sa.Column('notify_on_investment', sa.Boolean(), nullable=True),
        sa.Column('max_weekly_roundup', sa.Float(), nullable=True),
        sa.Column('max_monthly_micro_invest', sa.Float(), nullable=True),
        sa.Column('completed_micro_invest_education', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['micro_invest_portfolio_id'], ['portfolios.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_user_settings_id'), 'user_settings', ['id'], unique=False)
    
    # Set default values for new trades columns
    op.execute("UPDATE trades SET is_fractional = FALSE WHERE is_fractional IS NULL")
    op.execute("UPDATE trades SET investment_type = 'standard' WHERE investment_type IS NULL")
    op.execute("UPDATE trades SET order_type = 'market' WHERE order_type IS NULL")
    op.execute("UPDATE trades SET trade_source = 'user_initiated' WHERE trade_source IS NULL")


def downgrade():
    # Drop the foreign keys first
    op.drop_constraint('fk_trades_recurring_investment', 'trades', type_='foreignkey')
    
    # Drop tables
    op.drop_index(op.f('ix_user_settings_id'), table_name='user_settings')
    op.drop_table('user_settings')
    op.drop_index(op.f('ix_roundup_transactions_id'), table_name='roundup_transactions')
    op.drop_table('roundup_transactions')
    
    # Drop columns from trades table
    op.drop_column('trades', 'metadata')
    op.drop_column('trades', 'recurring_investment_id')
    op.drop_column('trades', 'filled_price')
    op.drop_column('trades', 'filled_quantity')
    op.drop_column('trades', 'total_amount')
    op.drop_column('trades', 'trade_source')
    op.drop_column('trades', 'order_type')
    op.drop_column('trades', 'investment_type')
    op.drop_column('trades', 'investment_amount')
    op.drop_column('trades', 'is_fractional')
    
    # Make quantity non-nullable again
    op.alter_column('trades', 'quantity', existing_type=sa.Float(), nullable=False)
    
    # Drop enum types
    micro_invest_target = sa.Enum('default_portfolio', 'specific_portfolio', 'specific_symbol', 'recommended_etf', name='microinvesttarget')
    micro_invest_target.drop(op.get_bind())
    
    roundup_frequency = sa.Enum('daily', 'weekly', 'threshold', name='roundupfrequency')
    roundup_frequency.drop(op.get_bind())
    
    order_type = sa.Enum('market', 'limit', name='ordertype')
    order_type.drop(op.get_bind())
    
    trade_source = sa.Enum('user_initiated', 'recurring', 'roundup', 'auto_invest', 'micro_deposit', name='tradesource')
    trade_source.drop(op.get_bind())
    
    investment_type = sa.Enum('standard', 'dollar_based', 'micro', 'roundup', name='investmenttype')
    investment_type.drop(op.get_bind())
    
    # Note: Cannot remove value from enum in PostgreSQL, so we leave 'pending_approval' in tradestatus