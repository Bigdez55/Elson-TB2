"""Add PayPal payment support fields to subscription model

Revision ID: 20250401_add_paypal_support
Revises: 20250324_add_micro_investing_models
Create Date: 2025-04-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, Column, String, JSON, Integer, DateTime, ForeignKey
from sqlalchemy.sql import text
import json

# revision identifiers
revision = '20250401_add_paypal_support'
down_revision = '20250324_add_micro_investing_models'
branch_labels = None
depends_on = None

def get_connection_dialect():
    """Determine if we're using SQLite or PostgreSQL"""
    conn = op.get_bind()
    inspector = inspect(conn)
    return inspector.dialect.name

def upgrade():
    # Add PayPal-specific fields to subscriptions table
    op.add_column('subscriptions', sa.Column('paypal_agreement_id', sa.String(), nullable=True))
    op.add_column('subscriptions', sa.Column('paypal_payer_id', sa.String(), nullable=True))
    
    # Add indexes to optimize subscription queries
    op.create_index(op.f('ix_subscriptions_payment_method_id'), 'subscriptions', ['payment_method_id'], unique=False)
    op.create_index(op.f('ix_subscriptions_plan'), 'subscriptions', ['plan'], unique=False)
    
    # Handle JSONB column differently for SQLite vs PostgreSQL
    dialect = get_connection_dialect()
    if dialect == 'postgresql':
        from sqlalchemy.dialects import postgresql
        # Add subscription_history table with PostgreSQL JSONB
        op.create_table('subscription_history',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('subscription_id', sa.Integer(), nullable=False),
            sa.Column('change_type', sa.String(), nullable=False),
            sa.Column('change_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('changed_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    else:
        # For SQLite, use TEXT to store JSON
        op.create_table('subscription_history',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('subscription_id', sa.Integer(), nullable=False),
            sa.Column('change_type', sa.String(), nullable=False),
            sa.Column('change_data', sa.Text(), nullable=True),  # SQLite doesn't have native JSON, use TEXT
            sa.Column('changed_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    
    op.create_index(op.f('ix_subscription_history_subscription_id'), 'subscription_history', ['subscription_id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_subscription_history_subscription_id'), table_name='subscription_history')
    op.drop_table('subscription_history')
    op.drop_index(op.f('ix_subscriptions_plan'), table_name='subscriptions')
    op.drop_index(op.f('ix_subscriptions_payment_method_id'), table_name='subscriptions')
    op.drop_column('subscriptions', 'paypal_payer_id')
    op.drop_column('subscriptions', 'paypal_agreement_id')