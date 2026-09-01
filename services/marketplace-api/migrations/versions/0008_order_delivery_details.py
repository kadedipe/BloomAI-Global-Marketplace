"""Add delivery and contact details to marketplace orders.

Revision ID: 0008_order_delivery_details
Revises: 0007_profile_photos
"""

from alembic import op
import sqlalchemy as sa

revision = "0008_order_delivery_details"
down_revision = "0007_profile_photos"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("recipient_name", sa.String(length=120), nullable=True))
    op.add_column("orders", sa.Column("phone", sa.String(length=40), nullable=True))
    op.add_column("orders", sa.Column("address_line1", sa.String(length=240), nullable=True))
    op.add_column("orders", sa.Column("city", sa.String(length=120), nullable=True))
    op.add_column("orders", sa.Column("region", sa.String(length=120), nullable=True))
    op.add_column("orders", sa.Column("postal_code", sa.String(length=32), nullable=True))
    op.add_column("orders", sa.Column("country", sa.String(length=120), nullable=True))
    op.add_column("orders", sa.Column("buyer_note", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("orders", "buyer_note")
    op.drop_column("orders", "country")
    op.drop_column("orders", "postal_code")
    op.drop_column("orders", "region")
    op.drop_column("orders", "city")
    op.drop_column("orders", "address_line1")
    op.drop_column("orders", "phone")
    op.drop_column("orders", "recipient_name")
