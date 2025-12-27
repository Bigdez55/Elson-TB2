"""add_subscription_payments_history_tables

Revision ID: 0c1cc482b9b3
Revises: 7a32be28d1fe
Create Date: 2025-07-13 23:36:43.345263

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0c1cc482b9b3"
down_revision: Union[str, Sequence[str], None] = "7a32be28d1fe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create subscription_payments table
    op.create_table(
        "subscription_payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("subscription_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "SUCCEEDED",
                "FAILED",
                "REFUNDED",
                "CANCELED",
                name="paymentstatus",
            ),
            nullable=False,
        ),
        sa.Column("payment_date", sa.DateTime(), nullable=False),
        sa.Column("provider_payment_id", sa.String(), nullable=True),
        sa.Column("provider_payment_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["subscriptions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_subscription_payments_id"),
        "subscription_payments",
        ["id"],
        unique=False,
    )

    # Create subscription_history table
    op.create_table(
        "subscription_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("subscription_id", sa.Integer(), nullable=False),
        sa.Column("change_type", sa.String(), nullable=False),
        sa.Column("change_data", sa.JSON(), nullable=True),
        sa.Column("changed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["subscriptions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_subscription_history_id"), "subscription_history", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_subscription_history_subscription_id"),
        "subscription_history",
        ["subscription_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop subscription tables in reverse order
    op.drop_index(
        op.f("ix_subscription_history_subscription_id"),
        table_name="subscription_history",
    )
    op.drop_index(op.f("ix_subscription_history_id"), table_name="subscription_history")
    op.drop_table("subscription_history")

    op.drop_index(
        op.f("ix_subscription_payments_id"), table_name="subscription_payments"
    )
    op.drop_table("subscription_payments")
