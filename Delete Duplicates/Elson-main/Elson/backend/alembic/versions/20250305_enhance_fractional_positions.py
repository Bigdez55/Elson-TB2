"""enhance fractional positions

Revision ID: 20250305_enhance_fractional_positions
Revises: 20240301_add_fractional_share_support
Create Date: 2025-03-05 20:18:30.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250305_enhance_fractional_positions'
down_revision = '20240301_add_fractional_share_support'
branch_labels = None
depends_on = None


def upgrade():
    # ### Update positions table to use Numeric type for precision ###
    op.alter_column('positions', 'quantity',
                   type_=sa.Numeric(precision=16, scale=8),
                   existing_type=sa.Float(),
                   nullable=False)
                   
    op.alter_column('positions', 'average_price',
                   type_=sa.Numeric(precision=16, scale=8),
                   existing_type=sa.Float(),
                   nullable=False)
                   
    op.alter_column('positions', 'current_price',
                   type_=sa.Numeric(precision=16, scale=8),
                   existing_type=sa.Float(),
                   nullable=True)
                   
    op.alter_column('positions', 'unrealized_pl',
                   type_=sa.Numeric(precision=16, scale=2),
                   existing_type=sa.Float(),
                   nullable=True)
                   
    # Add is_fractional flag to positions
    op.add_column('positions', sa.Column('is_fractional', sa.Boolean(),
                                         nullable=False, server_default='false'))
    
    # Add cost_basis column (separate from calculated property)
    op.add_column('positions', sa.Column('cost_basis', sa.Numeric(precision=16, scale=2),
                                         nullable=True))
    
    # Add market_value column (separate from calculated property)
    op.add_column('positions', sa.Column('market_value', sa.Numeric(precision=16, scale=2),
                                         nullable=True))
                                         
    # Add minimum_investment column for dollar-based minimums
    op.add_column('positions', sa.Column('minimum_investment', sa.Numeric(precision=10, scale=2),
                                          nullable=True))
                                          
    # Add last_trade_date for tracking when position was last updated
    op.add_column('positions', sa.Column('last_trade_date', sa.DateTime(),
                                          nullable=True))
    
    # Add indices for faster querying
    op.create_index(op.f('ix_positions_symbol'), 'positions', ['symbol'], unique=False)
    op.create_index(op.f('ix_positions_portfolio_id_symbol'), 'positions',
                     ['portfolio_id', 'symbol'], unique=True)


def downgrade():
    # Drop indices
    op.drop_index(op.f('ix_positions_portfolio_id_symbol'), table_name='positions')
    op.drop_index(op.f('ix_positions_symbol'), table_name='positions')
    
    # Drop columns
    op.drop_column('positions', 'last_trade_date')
    op.drop_column('positions', 'minimum_investment')
    op.drop_column('positions', 'market_value')
    op.drop_column('positions', 'cost_basis')
    op.drop_column('positions', 'is_fractional')
    
    # Revert type changes
    op.alter_column('positions', 'unrealized_pl',
                   type_=sa.Float(),
                   existing_type=sa.Numeric(precision=16, scale=2),
                   nullable=True)
                   
    op.alter_column('positions', 'current_price',
                   type_=sa.Float(),
                   existing_type=sa.Numeric(precision=16, scale=8),
                   nullable=True)
                   
    op.alter_column('positions', 'average_price',
                   type_=sa.Float(),
                   existing_type=sa.Numeric(precision=16, scale=8),
                   nullable=False)
                   
    op.alter_column('positions', 'quantity',
                   type_=sa.Float(),
                   existing_type=sa.Numeric(precision=16, scale=8),
                   nullable=False)