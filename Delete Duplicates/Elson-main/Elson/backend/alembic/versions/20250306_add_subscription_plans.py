"""Add subscription plans and payment tracking

Revision ID: 20250306_add_subscription_plans
Revises: 20250305_add_executed_by_field
Create Date: 2025-03-06 10:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250306_add_subscription_plans'
down_revision = '20250305_add_executed_by_field'
branch_labels = None
depends_on = None


def upgrade():
    # Create subscription plan and billing cycle enums
    subscription_plan_enum = postgresql.ENUM('free', 'premium', 'family', name='subscriptionplan')
    op.create_type('subscriptionplan', ["free", "premium", "family"])
    
    billing_cycle_enum = postgresql.ENUM('monthly', 'annually', name='billingcycle')
    op.create_type('billingcycle', ["monthly", "annually"])
    
    payment_status_enum = postgresql.ENUM('pending', 'succeeded', 'failed', 'refunded', 'canceled', name='paymentstatus')
    op.create_type('paymentstatus', ["pending", "succeeded", "failed", "refunded", "canceled"])
    
    payment_method_enum = postgresql.ENUM('credit_card', 'bank_account', 'paypal', 'apple_pay', 'google_pay', name='paymentmethod')
    op.create_type('paymentmethod', ["credit_card", "bank_account", "paypal", "apple_pay", "google_pay"])
    
    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('plan', subscription_plan_enum, nullable=False),
        sa.Column('billing_cycle', billing_cycle_enum, nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('auto_renew', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('trial_end_date', sa.DateTime(), nullable=True),
        sa.Column('payment_method_id', sa.String(), nullable=True),
        sa.Column('payment_method_type', payment_method_enum, nullable=True),
        sa.Column('encrypted_payment_details', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('canceled_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscriptions_id'), 'subscriptions', ['id'], unique=False)
    op.create_index(op.f('ix_subscriptions_user_id'), 'subscriptions', ['user_id'], unique=False)
    
    # Create subscription payments table
    op.create_table(
        'subscription_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('subscription_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('status', payment_status_enum, nullable=False),
        sa.Column('payment_date', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('provider_payment_id', sa.String(), nullable=True),
        sa.Column('provider_payment_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscription_payments_id'), 'subscription_payments', ['id'], unique=False)
    op.create_index(op.f('ix_subscription_payments_subscription_id'), 'subscription_payments', ['subscription_id'], unique=False)


def downgrade():
    # Drop tables
    op.drop_table('subscription_payments')
    op.drop_table('subscriptions')
    
    # Drop enums
    op.execute('DROP TYPE paymentmethod')
    op.execute('DROP TYPE paymentstatus')
    op.execute('DROP TYPE billingcycle')
    op.execute('DROP TYPE subscriptionplan')