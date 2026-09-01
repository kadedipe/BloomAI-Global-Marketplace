"""Add reservation, pricing, tracking and refund reconciliation fields.

Revision ID: 0010_commerce_hardening
Revises: 0009_commerce_fulfillment
"""

from alembic import op
import sqlalchemy as sa

revision = "0010_commerce_hardening"
down_revision = "0009_commerce_fulfillment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("subtotal", sa.Numeric(12, 2), nullable=True))
    op.add_column("orders", sa.Column("shipping_amount", sa.Numeric(12, 2), nullable=False, server_default="0"))
    op.add_column("orders", sa.Column("tax_amount", sa.Numeric(12, 2), nullable=False, server_default="0"))
    op.add_column("orders", sa.Column("reservation_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("orders", sa.Column("tracking_provider_id", sa.String(length=160), nullable=True))
    op.add_column("orders", sa.Column("tracking_status", sa.String(length=80), nullable=True))
    op.add_column("orders", sa.Column("tracking_updated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("orders", sa.Column("refund_provider_status", sa.String(length=80), nullable=True))
    op.add_column("orders", sa.Column("refund_reference", sa.String(length=160), nullable=True))
    op.create_index("ix_orders_reservation_expires_at", "orders", ["reservation_expires_at"], unique=False)
    op.execute("UPDATE orders SET subtotal = total WHERE subtotal IS NULL")


def downgrade() -> None:
    op.drop_index("ix_orders_reservation_expires_at", table_name="orders")
    op.drop_column("orders", "refund_reference")
    op.drop_column("orders", "refund_provider_status")
    op.drop_column("orders", "tracking_updated_at")
    op.drop_column("orders", "tracking_status")
    op.drop_column("orders", "tracking_provider_id")
    op.drop_column("orders", "reservation_expires_at")
    op.drop_column("orders", "tax_amount")
    op.drop_column("orders", "shipping_amount")
    op.drop_column("orders", "subtotal")
