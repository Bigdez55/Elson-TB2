"""add two-factor auth fields

Revision ID: 20240229_add_two_factor_auth
Revises: 20240229_add_custodial_accounts
Create Date: 2024-02-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20240229_add_two_factor_auth'
down_revision = '20240229_add_custodial_accounts'
branch_labels = None
depends_on = None


def upgrade():
    # Add two-factor authentication fields to users table
    op.add_column('users', sa.Column('two_factor_enabled', sa.Boolean(), nullable=True, default=False))
    op.add_column('users', sa.Column('two_factor_secret', sa.String(), nullable=True))
    op.add_column('users', sa.Column('two_factor_backup_codes', postgresql.ARRAY(sa.String()), nullable=True))
    
    # Add account security fields to users table
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=True, default=0))
    op.add_column('users', sa.Column('account_locked_until', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('password_last_changed', sa.DateTime(), nullable=True))


def downgrade():
    # Remove two-factor authentication fields from users table
    op.drop_column('users', 'two_factor_enabled')
    op.drop_column('users', 'two_factor_secret')
    op.drop_column('users', 'two_factor_backup_codes')
    
    # Remove account security fields from users table
    op.drop_column('users', 'failed_login_attempts')
    op.drop_column('users', 'account_locked_until')
    op.drop_column('users', 'password_last_changed')