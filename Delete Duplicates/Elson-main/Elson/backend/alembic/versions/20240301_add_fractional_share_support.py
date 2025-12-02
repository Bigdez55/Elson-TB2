"""add fractional share support

Revision ID: 20240301_add_fractional_share_support
Revises: 20240229_add_two_factor_auth
Create Date: 2024-03-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20240301_add_fractional_share_support'
down_revision = '20240229_add_two_factor_auth'
branch_labels = None
depends_on = None


def upgrade():
    # ### Add new enum types ###
    investment_type = postgresql.ENUM('quantity_based', 'dollar_based', name='investmenttype')
    investment_type.create(op.get_bind())
    
    trade_source = postgresql.ENUM('user_initiated', 'auto_investment', 'rebalancing', 
                                   'dividend_reinvestment', 'aggregated', name='tradesource')
    trade_source.create(op.get_bind())
    
    # Update trade status enum to add partially_filled
    op.execute("ALTER TYPE tradestatus ADD VALUE 'partially_filled' AFTER 'filled'")
    
    # ### Add columns to trades table ###
    op.add_column('trades', sa.Column('filled_quantity', sa.Numeric(precision=16, scale=8), nullable=True))
    op.add_column('trades', sa.Column('average_price', sa.Numeric(precision=16, scale=8), nullable=True))
    op.add_column('trades', sa.Column('commission', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('trades', sa.Column('investment_amount', sa.Numeric(precision=16, scale=2), nullable=True))
    op.add_column('trades', sa.Column('investment_type', sa.Enum('quantity_based', 'dollar_based', 
                                                                 name='investmenttype'), 
                                      nullable=False, server_default='quantity_based'))
    op.add_column('trades', sa.Column('is_fractional', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('trades', sa.Column('parent_order_id', sa.Integer(), nullable=True))
    op.add_column('trades', sa.Column('minimum_quantity', sa.Numeric(precision=16, scale=8), nullable=True))
    op.add_column('trades', sa.Column('trade_source', sa.Enum('user_initiated', 'auto_investment', 
                                                              'rebalancing', 'dividend_reinvestment', 
                                                              'aggregated', name='tradesource'), 
                                      nullable=False, server_default='user_initiated'))
    op.add_column('trades', sa.Column('broker_order_id', sa.String(length=50), nullable=True))
    op.add_column('trades', sa.Column('broker_account_id', sa.String(length=50), nullable=True))
    op.add_column('trades', sa.Column('broker_status', sa.String(length=50), nullable=True))
    op.add_column('trades', sa.Column('settlement_date', sa.DateTime(), nullable=True))
    
    # Add foreign key for parent_order_id
    op.create_foreign_key(None, 'trades', 'trades', ['parent_order_id'], ['id'])
    
    # Change quantity and price columns to be nullable
    op.alter_column('trades', 'quantity', nullable=True)
    op.alter_column('trades', 'price', nullable=True)
    
    # Alter the type of quantity, price, and total_amount to Numeric for precision
    op.alter_column('trades', 'quantity', 
                    type_=sa.Numeric(precision=16, scale=8), 
                    existing_type=sa.Float(), 
                    nullable=True)
    op.alter_column('trades', 'price', 
                    type_=sa.Numeric(precision=16, scale=8), 
                    existing_type=sa.Float(), 
                    nullable=True)
    op.alter_column('trades', 'total_amount', 
                    type_=sa.Numeric(precision=16, scale=2), 
                    existing_type=sa.Float(), 
                    nullable=True)
    
    # Add index for faster queries
    op.create_index(op.f('ix_trades_parent_order_id'), 'trades', ['parent_order_id'], unique=False)
    op.create_index(op.f('ix_trades_symbol'), 'trades', ['symbol'], unique=False)
    op.create_index(op.f('ix_trades_broker_order_id'), 'trades', ['broker_order_id'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_trades_broker_order_id'), table_name='trades')
    op.drop_index(op.f('ix_trades_symbol'), table_name='trades')
    op.drop_index(op.f('ix_trades_parent_order_id'), table_name='trades')
    
    # Drop foreign key
    op.drop_constraint(None, 'trades', type_='foreignkey')
    
    # Drop columns
    op.drop_column('trades', 'settlement_date')
    op.drop_column('trades', 'broker_status')
    op.drop_column('trades', 'broker_account_id')
    op.drop_column('trades', 'broker_order_id')
    op.drop_column('trades', 'trade_source')
    op.drop_column('trades', 'minimum_quantity')
    op.drop_column('trades', 'parent_order_id')
    op.drop_column('trades', 'is_fractional')
    op.drop_column('trades', 'investment_type')
    op.drop_column('trades', 'investment_amount')
    op.drop_column('trades', 'commission')
    op.drop_column('trades', 'average_price')
    op.drop_column('trades', 'filled_quantity')
    
    # Convert column types back
    op.alter_column('trades', 'total_amount', 
                   type_=sa.Float(), 
                   existing_type=sa.Numeric(precision=16, scale=2), 
                   nullable=False)
    op.alter_column('trades', 'price', 
                   type_=sa.Float(), 
                   existing_type=sa.Numeric(precision=16, scale=8), 
                   nullable=False)
    op.alter_column('trades', 'quantity', 
                   type_=sa.Float(), 
                   existing_type=sa.Numeric(precision=16, scale=8), 
                   nullable=False)
    
    # Make quantity and price non-nullable again
    op.alter_column('trades', 'quantity', nullable=False)
    op.alter_column('trades', 'price', nullable=False)
    
    # Drop enum types
    op.execute("DROP TYPE tradesource")
    op.execute("DROP TYPE investmenttype")
    
    # Can't easily remove an enum value, would require recreating the type in Postgres