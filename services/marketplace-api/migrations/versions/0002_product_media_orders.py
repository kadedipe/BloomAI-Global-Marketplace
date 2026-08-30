"""Add managed product media and Paystack orders."""

from alembic import op
import sqlalchemy as sa

revision = "0002_product_media_orders"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("image_public_id", sa.String(512), nullable=True))
    order_status = sa.Enum("pending", "paid", "failed", "cancelled", name="orderstatus")
    order_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reference", sa.String(100), nullable=False),
        sa.Column("buyer_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", order_status, nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("provider_transaction_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_orders_reference", "orders", ["reference"], unique=True)
    op.create_index("ix_orders_buyer_id", "orders", ["buyer_id"])
    op.create_index("ix_orders_product_id", "orders", ["product_id"])


def downgrade() -> None:
    op.drop_table("orders")
    op.drop_column("products", "image_public_id")
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TYPE IF EXISTS orderstatus")
