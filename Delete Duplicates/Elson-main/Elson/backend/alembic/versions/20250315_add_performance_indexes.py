"""Add performance indexes

Revision ID: 20250315_add_performance_indexes
Revises: 20250310_add_educational_models
Create Date: 2025-03-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250315_add_performance_indexes'
down_revision = '20250310_add_educational_models'
branch_labels = None
depends_on = None


def upgrade():
    # Add indexes to improve query performance
    
    # Position table indexes
    op.create_index('idx_position_market_value', 'positions', ['market_value'], unique=False)
    op.create_index('idx_position_unrealized_pl', 'positions', ['unrealized_pl'], unique=False)
    op.create_index('idx_position_created_at', 'positions', ['created_at'], unique=False)
    op.create_index('idx_position_updated_at', 'positions', ['updated_at'], unique=False)
    op.create_index('idx_position_last_trade_date', 'positions', ['last_trade_date'], unique=False)
    op.create_index('idx_position_sector', 'positions', ['sector'], unique=False)
    op.create_index('idx_position_asset_class', 'positions', ['asset_class'], unique=False)
    
    # Trade table indexes
    op.create_index('idx_trade_executed_at', 'trades', ['executed_at'], unique=False)
    op.create_index('idx_trade_created_at', 'trades', ['created_at'], unique=False)
    op.create_index('idx_trade_status', 'trades', ['status'], unique=False)
    op.create_index('idx_trade_symbol', 'trades', ['symbol'], unique=False)
    op.create_index('idx_trade_trade_source', 'trades', ['trade_source'], unique=False)
    op.create_index('idx_trade_portfolio_symbol', 'trades', ['portfolio_id', 'symbol'], unique=False)
    op.create_index('idx_trade_port_status_date', 'trades', ['portfolio_id', 'status', 'executed_at'], unique=False)
    
    # Portfolio table indexes
    op.create_index('idx_portfolio_updated_at', 'portfolios', ['updated_at'], unique=False)
    op.create_index('idx_portfolio_last_rebalanced_at', 'portfolios', ['last_rebalanced_at'], unique=False)
    op.create_index('idx_portfolio_risk_profile', 'portfolios', ['risk_profile'], unique=False)
    
    # User and Account related indexes
    op.create_index('idx_user_verified', 'users', ['is_verified'], unique=False)
    op.create_index('idx_user_active', 'users', ['is_active'], unique=False)
    op.create_index('idx_user_role', 'users', ['role'], unique=False)
    op.create_index('idx_account_type', 'accounts', ['account_type'], unique=False)
    op.create_index('idx_account_status', 'accounts', ['status'], unique=False)


def downgrade():
    # Remove indexes
    
    # Position table indexes
    op.drop_index('idx_position_market_value', table_name='positions')
    op.drop_index('idx_position_unrealized_pl', table_name='positions')
    op.drop_index('idx_position_created_at', table_name='positions')
    op.drop_index('idx_position_updated_at', table_name='positions')
    op.drop_index('idx_position_last_trade_date', table_name='positions')
    op.drop_index('idx_position_sector', table_name='positions')
    op.drop_index('idx_position_asset_class', table_name='positions')
    
    # Trade table indexes
    op.drop_index('idx_trade_executed_at', table_name='trades')
    op.drop_index('idx_trade_created_at', table_name='trades')
    op.drop_index('idx_trade_status', table_name='trades')
    op.drop_index('idx_trade_symbol', table_name='trades')
    op.drop_index('idx_trade_trade_source', table_name='trades')
    op.drop_index('idx_trade_portfolio_symbol', table_name='trades')
    op.drop_index('idx_trade_port_status_date', table_name='trades')
    
    # Portfolio table indexes
    op.drop_index('idx_portfolio_updated_at', table_name='portfolios')
    op.drop_index('idx_portfolio_last_rebalanced_at', table_name='portfolios')
    op.drop_index('idx_portfolio_risk_profile', table_name='portfolios')
    
    # User and Account related indexes
    op.drop_index('idx_user_verified', table_name='users')
    op.drop_index('idx_user_active', table_name='users')
    op.drop_index('idx_user_role', table_name='users')
    op.drop_index('idx_account_type', table_name='accounts')
    op.drop_index('idx_account_status', table_name='accounts')