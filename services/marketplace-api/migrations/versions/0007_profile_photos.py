"""Add optional profile photos for marketplace users.

Revision ID: 0007_profile_photos
Revises: 0006_notification_preferences
"""

from alembic import op
import sqlalchemy as sa

revision = "0007_profile_photos"
down_revision = "0006_notification_preferences"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar_url", sa.String(length=2048), nullable=True))
    op.add_column("users", sa.Column("avatar_public_id", sa.String(length=512), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "avatar_public_id")
    op.drop_column("users", "avatar_url")
