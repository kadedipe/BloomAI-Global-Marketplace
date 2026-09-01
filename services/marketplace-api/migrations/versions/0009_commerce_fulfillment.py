"""Add inventory, fulfillment and refund workflow fields.

Revision ID: 0009_commerce_fulfillment
Revises: 0008_order_delivery_details
"""

from alembic import op
import sqlalchemy as sa

revision = "0009_commerce_fulfillment"
down_revision = "0008_order_delivery_details"
branch_labels = None
depends_on = None

fulfillment_status = sa.Enum(
    "unfulfilled", "processing", "shipped", "delivered", "cancelled",
    name="fulfillmentstatus",
)
refund_status = sa.Enum(
    "none", "requested", "approved", "processing", "refunded", "rejected",
    name="refundstatus",
)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        fulfillment_status.create(bind, checkfirst=True)
        refund_status.create(bind, checkfirst=True)

    op.add_column("products", sa.Column("inventory_quantity", sa.Integer(), nullable=True))
    op.add_column(
        "products",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "orders",
        sa.Column("inventory_reserved", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "orders",
        sa.Column(
            "fulfillment_status",
            fulfillment_status,
            nullable=False,
            server_default="unfulfilled",
        ),
    )
    op.add_column("orders", sa.Column("carrier", sa.String(length=120), nullable=True))
    op.add_column("orders", sa.Column("tracking_number", sa.String(length=160), nullable=True))
    op.add_column("orders", sa.Column("shipped_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("orders", sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "orders",
        sa.Column("refund_status", refund_status, nullable=False, server_default="none"),
    )
    op.add_column("orders", sa.Column("refund_reason", sa.Text(), nullable=True))
    op.add_column("orders", sa.Column("refund_requested_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("orders", sa.Column("refund_processed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("orders", "refund_processed_at")
    op.drop_column("orders", "refund_requested_at")
    op.drop_column("orders", "refund_reason")
    op.drop_column("orders", "refund_status")
    op.drop_column("orders", "delivered_at")
    op.drop_column("orders", "shipped_at")
    op.drop_column("orders", "tracking_number")
    op.drop_column("orders", "carrier")
    op.drop_column("orders", "fulfillment_status")
    op.drop_column("orders", "inventory_reserved")
    op.drop_column("products", "is_active")
    op.drop_column("products", "inventory_quantity")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        refund_status.drop(bind, checkfirst=True)
        fulfillment_status.drop(bind, checkfirst=True)
