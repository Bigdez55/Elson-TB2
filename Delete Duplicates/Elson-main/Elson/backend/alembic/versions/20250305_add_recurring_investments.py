"""add recurring investments

Revision ID: 20250305_add_recurring_investments
Revises: 20250305_enhance_fractional_positions
Create Date: 2025-03-05 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250305_add_recurring_investments'
down_revision = '20250305_enhance_fractional_positions'
branch_labels = None
depends_on = None


def upgrade():
    # Create RecurringFrequency enum type
    recurring_frequency = sa.Enum('daily', 'weekly', 'monthly', 'quarterly', name='recurringfrequency')
    recurring_frequency.create(op.get_bind())
    
    # Create recurring_investments table
    op.create_table(
        'recurring_investments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('portfolio_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('investment_amount', sa.Numeric(precision=16, scale=2), nullable=False),
        sa.Column('frequency', sa.Enum('daily', 'weekly', 'monthly', 'quarterly', name='recurringfrequency'), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('next_investment_date', sa.DateTime(), nullable=False),
        sa.Column('last_execution_date', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('execution_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recurring_investments_id'), 'recurring_investments', ['id'], unique=False)
    
    # Update TradeSource enum in the trades table
    # First, rename the old enum type
    op.execute("ALTER TYPE tradesource RENAME TO tradesource_old")
    
    # Create the new enum type with "recurring" instead of "auto_investment"
    tradesource = sa.Enum('user_initiated', 'recurring', 'rebalancing', 
                           'dividend_reinvestment', 'aggregated', name='tradesource')
    tradesource.create(op.get_bind())
    
    # Update the column to use the new enum type
    op.execute("ALTER TABLE trades ALTER COLUMN trade_source TYPE tradesource USING trade_source::text::tradesource")
    
    # Drop the old enum type
    op.execute("DROP TYPE tradesource_old")
    
    # Add column to link trades to recurring investments
    op.add_column('trades', sa.Column('recurring_investment_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'trades', 'recurring_investments', ['recurring_investment_id'], ['id'])


def downgrade():
    # Drop foreign key constraint first
    op.drop_constraint(None, 'trades', type_='foreignkey')
    
    # Drop the recurring_investment_id column
    op.drop_column('trades', 'recurring_investment_id')
    
    # Revert the TradeSource enum back
    op.execute("ALTER TYPE tradesource RENAME TO tradesource_old")
    
    # Create the original enum type
    tradesource = sa.Enum('user_initiated', 'auto_investment', 'rebalancing', 
                           'dividend_reinvestment', 'aggregated', name='tradesource')
    tradesource.create(op.get_bind())
    
    # Update the column to use the original enum type
    op.execute("ALTER TABLE trades ALTER COLUMN trade_source TYPE tradesource USING " +
               "CASE WHEN trade_source::text = 'recurring' THEN 'auto_investment'::tradesource " +
               "ELSE trade_source::text::tradesource END")
    
    # Drop the temporary enum type
    op.execute("DROP TYPE tradesource_old")
    
    # Drop the recurring_investments table
    op.drop_index(op.f('ix_recurring_investments_id'), table_name='recurring_investments')
    op.drop_table('recurring_investments')
    
    # Drop the RecurringFrequency enum type
    op.execute("DROP TYPE recurringfrequency")