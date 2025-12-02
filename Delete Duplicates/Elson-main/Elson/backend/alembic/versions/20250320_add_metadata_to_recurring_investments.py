"""add metadata to recurring investments

Revision ID: 20250320_add_metadata_to_recurring_investments
Revises: 20250315_add_performance_indexes
Create Date: 2025-03-20 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250320_add_metadata_to_recurring_investments'
down_revision = '20250315_add_performance_indexes'
branch_labels = None
depends_on = None


def upgrade():
    # Add metadata column to recurring_investments table
    op.add_column('recurring_investments',
                 sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    
    # Create index for improved query performance on metadata
    op.create_index('idx_recurring_investments_metadata', 'recurring_investments', ['metadata'], 
                    postgresql_using='gin')


def downgrade():
    # Drop the index
    op.drop_index('idx_recurring_investments_metadata', table_name='recurring_investments')
    
    # Drop the column
    op.drop_column('recurring_investments', 'metadata')