"""Add query optimization indexes

Revision ID: 20250320_add_query_optimization_indexes
Revises: 20250320_add_metadata_to_recurring_investments
Create Date: 2025-03-22 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250320_add_query_optimization_indexes'
down_revision = '20250320_add_metadata_to_recurring_investments'
branch_labels = None
depends_on = None


def upgrade():
    # Add additional indexes for query optimization
    
    # Trade indexes
    op.create_index('idx_trade_user_id', 'trades', ['user_id'])
    op.create_index('idx_trade_investment_type', 'trades', ['investment_type'])
    op.create_index('idx_trade_user_id_symbol', 'trades', ['user_id', 'symbol'])
    op.create_index('idx_trade_user_id_portfolio_id', 'trades', ['user_id', 'portfolio_id'])
    op.create_index('idx_trade_user_id_status', 'trades', ['user_id', 'status'])
    op.create_index('idx_trade_user_id_investment_type', 'trades', ['user_id', 'investment_type'])
    
    # User indexes
    op.create_index('idx_user_email', 'users', ['email'])
    
    # Portfolio indexes
    op.create_index('idx_portfolio_user_id', 'portfolios', ['user_id'])
    op.create_index('idx_portfolio_guardian_id', 'portfolios', ['guardian_id'])
    
    # RecurringInvestment indexes
    op.create_index('idx_recurring_investment_user_id', 'recurring_investments', ['user_id'])
    op.create_index('idx_recurring_investment_portfolio_id', 'recurring_investments', ['portfolio_id'])
    op.create_index('idx_recurring_investment_is_active', 'recurring_investments', ['is_active'])
    op.create_index('idx_recurring_investment_next_date', 'recurring_investments', ['next_investment_date'])
    op.create_index('idx_recurring_investment_user_active', 'recurring_investments', ['user_id', 'is_active'])
    op.create_index('idx_recurring_investment_next_date_active', 'recurring_investments', ['next_investment_date', 'is_active'])
    
    # Notification indexes
    op.create_index('idx_notification_user_id', 'notifications', ['user_id'])
    op.create_index('idx_notification_is_read', 'notifications', ['is_read'])
    op.create_index('idx_notification_created_at', 'notifications', ['created_at'])
    op.create_index('idx_notification_user_id_is_read', 'notifications', ['user_id', 'is_read'])


def downgrade():
    # Remove additional indexes
    
    # Trade indexes
    op.drop_index('idx_trade_user_id', table_name='trades')
    op.drop_index('idx_trade_investment_type', table_name='trades')
    op.drop_index('idx_trade_user_id_symbol', table_name='trades')
    op.drop_index('idx_trade_user_id_portfolio_id', table_name='trades')
    op.drop_index('idx_trade_user_id_status', table_name='trades')
    op.drop_index('idx_trade_user_id_investment_type', table_name='trades')
    
    # User indexes
    op.drop_index('idx_user_email', table_name='users')
    
    # Portfolio indexes
    op.drop_index('idx_portfolio_user_id', table_name='portfolios')
    op.drop_index('idx_portfolio_guardian_id', table_name='portfolios')
    
    # RecurringInvestment indexes
    op.drop_index('idx_recurring_investment_user_id', table_name='recurring_investments')
    op.drop_index('idx_recurring_investment_portfolio_id', table_name='recurring_investments')
    op.drop_index('idx_recurring_investment_is_active', table_name='recurring_investments')
    op.drop_index('idx_recurring_investment_next_date', table_name='recurring_investments')
    op.drop_index('idx_recurring_investment_user_active', table_name='recurring_investments')
    op.drop_index('idx_recurring_investment_next_date_active', table_name='recurring_investments')
    
    # Notification indexes
    op.drop_index('idx_notification_user_id', table_name='notifications')
    op.drop_index('idx_notification_is_read', table_name='notifications')
    op.drop_index('idx_notification_created_at', table_name='notifications')
    op.drop_index('idx_notification_user_id_is_read', table_name='notifications')