"""Add webauthn_credentials table for biometric authentication

Revision ID: add_webauthn_2025_12_06
Revises: efe8d9e3ce31
Create Date: 2025-12-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_webauthn_2025_12_06'
down_revision: Union[str, Sequence[str], None] = 'efe8d9e3ce31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add webauthn_credentials table"""
    op.create_table(
        'webauthn_credentials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('credential_id', sa.String(length=512), nullable=False),
        sa.Column('credential_name', sa.String(length=255), nullable=True),
        sa.Column('public_key', sa.Text(), nullable=False),
        sa.Column('sign_count', sa.Integer(), nullable=True),
        sa.Column('credential_type', sa.String(length=50), nullable=True),
        sa.Column('authenticator_type', sa.String(length=50), nullable=True),
        sa.Column('device_type', sa.String(length=100), nullable=True),
        sa.Column('aaguid', sa.String(length=36), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_used', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        op.f('ix_webauthn_credentials_id'),
        'webauthn_credentials',
        ['id'],
        unique=False
    )
    op.create_index(
        op.f('ix_webauthn_credentials_credential_id'),
        'webauthn_credentials',
        ['credential_id'],
        unique=True
    )


def downgrade() -> None:
    """Downgrade schema - remove webauthn_credentials table"""
    op.drop_index(
        op.f('ix_webauthn_credentials_credential_id'),
        table_name='webauthn_credentials'
    )
    op.drop_index(
        op.f('ix_webauthn_credentials_id'),
        table_name='webauthn_credentials'
    )
    op.drop_table('webauthn_credentials')
