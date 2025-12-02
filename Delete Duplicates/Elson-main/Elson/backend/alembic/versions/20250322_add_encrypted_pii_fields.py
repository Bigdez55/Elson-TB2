"""add encrypted pii fields

Revision ID: 20250322_add_encrypted_pii_fields
Revises: 20250321_add_notification_model
Create Date: 2025-03-22 17:05:23.967324

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
import sys
import os
import json

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the application's models and encryption utilities
from app.core.encryption import encrypt_sensitive_data

# revision identifiers, used by Alembic.
revision: str = '20250322_add_encrypted_pii_fields'
down_revision: Union[str, None] = '20250321_add_notification_model'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create new encrypted PII columns in User table
    op.add_column('users', sa.Column('_encrypted_email', sa.String(), nullable=True))
    op.add_column('users', sa.Column('_first_name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('_last_name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('_birthdate', sa.String(), nullable=True))
    op.add_column('users', sa.Column('_two_factor_secret', sa.String(), nullable=True))
    
    # Create new encrypted PII column in accounts table
    op.add_column('accounts', sa.Column('_encrypted_account_number', sa.String(), nullable=True))
    
    # Migrate existing data to encrypted fields
    # This needs to be done in a transaction
    connection = op.get_bind()
    session = Session(bind=connection)
    
    # Get all users
    users = connection.execute(sa.text('SELECT id, email, first_name, last_name, birthdate, two_factor_secret FROM users')).fetchall()
    
    # Encrypt and update each user's PII
    for user in users:
        user_id, email, first_name, last_name, birthdate, two_factor_secret = user
        
        # Encrypt email
        if email:
            encrypted_email = encrypt_sensitive_data(email)
            encrypted_email_json = json.dumps(encrypted_email)
            session.execute(
                sa.text('UPDATE users SET _encrypted_email = :encrypted_email WHERE id = :id'),
                {'encrypted_email': encrypted_email_json, 'id': user_id}
            )
        
        # Encrypt first_name
        if first_name:
            encrypted_first_name = encrypt_sensitive_data(first_name)
            encrypted_first_name_json = json.dumps(encrypted_first_name)
            session.execute(
                sa.text('UPDATE users SET _first_name = :encrypted_first_name WHERE id = :id'),
                {'encrypted_first_name': encrypted_first_name_json, 'id': user_id}
            )
        
        # Encrypt last_name
        if last_name:
            encrypted_last_name = encrypt_sensitive_data(last_name)
            encrypted_last_name_json = json.dumps(encrypted_last_name)
            session.execute(
                sa.text('UPDATE users SET _last_name = :encrypted_last_name WHERE id = :id'),
                {'encrypted_last_name': encrypted_last_name_json, 'id': user_id}
            )
        
        # Encrypt birthdate
        if birthdate:
            encrypted_birthdate = encrypt_sensitive_data(str(birthdate))
            encrypted_birthdate_json = json.dumps(encrypted_birthdate)
            session.execute(
                sa.text('UPDATE users SET _birthdate = :encrypted_birthdate WHERE id = :id'),
                {'encrypted_birthdate': encrypted_birthdate_json, 'id': user_id}
            )
        
        # Encrypt two_factor_secret
        if two_factor_secret:
            encrypted_two_factor_secret = encrypt_sensitive_data(two_factor_secret)
            encrypted_two_factor_secret_json = json.dumps(encrypted_two_factor_secret)
            session.execute(
                sa.text('UPDATE users SET _two_factor_secret = :encrypted_two_factor_secret WHERE id = :id'),
                {'encrypted_two_factor_secret': encrypted_two_factor_secret_json, 'id': user_id}
            )
    
    # Get all accounts
    accounts = connection.execute(sa.text('SELECT id, account_number FROM accounts')).fetchall()
    
    # Encrypt and update each account's PII
    for account in accounts:
        account_id, account_number = account
        
        # Encrypt account_number
        if account_number:
            encrypted_account_number = encrypt_sensitive_data(account_number)
            encrypted_account_number_json = json.dumps(encrypted_account_number)
            session.execute(
                sa.text('UPDATE accounts SET _encrypted_account_number = :encrypted_account_number WHERE id = :id'),
                {'encrypted_account_number': encrypted_account_number_json, 'id': account_id}
            )
    
    # Commit the transaction
    session.commit()


def downgrade() -> None:
    # Drop the encrypted columns
    op.drop_column('users', '_encrypted_email')
    op.drop_column('users', '_first_name')
    op.drop_column('users', '_last_name')
    op.drop_column('users', '_birthdate')
    op.drop_column('users', '_two_factor_secret')
    op.drop_column('accounts', '_encrypted_account_number')