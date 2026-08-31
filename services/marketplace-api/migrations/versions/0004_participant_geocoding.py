"""add participant geocoding fields

Revision ID: 0004_participant_geocoding
Revises: 0003_participant_segmentation
Create Date: 2026-08-31
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_participant_geocoding"
down_revision = "0003_participant_segmentation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("participant_profiles", sa.Column("address_line1", sa.String(length=180), nullable=True))
    op.add_column("participant_profiles", sa.Column("city", sa.String(length=100), nullable=True))
    op.add_column("participant_profiles", sa.Column("region", sa.String(length=100), nullable=True))
    op.add_column("participant_profiles", sa.Column("postal_code", sa.String(length=32), nullable=True))
    op.add_column("participant_profiles", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("participant_profiles", sa.Column("longitude", sa.Float(), nullable=True))
    op.add_column("participant_profiles", sa.Column("geocoding_source", sa.String(length=80), nullable=True))
    op.add_column("participant_profiles", sa.Column("geocoded_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_participant_profiles_city", "participant_profiles", ["city"], unique=False)
    op.create_index("ix_participant_profiles_region", "participant_profiles", ["region"], unique=False)
    op.create_index("ix_participant_profiles_latitude", "participant_profiles", ["latitude"], unique=False)
    op.create_index("ix_participant_profiles_longitude", "participant_profiles", ["longitude"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_participant_profiles_longitude", table_name="participant_profiles")
    op.drop_index("ix_participant_profiles_latitude", table_name="participant_profiles")
    op.drop_index("ix_participant_profiles_region", table_name="participant_profiles")
    op.drop_index("ix_participant_profiles_city", table_name="participant_profiles")
    op.drop_column("participant_profiles", "geocoded_at")
    op.drop_column("participant_profiles", "geocoding_source")
    op.drop_column("participant_profiles", "longitude")
    op.drop_column("participant_profiles", "latitude")
    op.drop_column("participant_profiles", "postal_code")
    op.drop_column("participant_profiles", "region")
    op.drop_column("participant_profiles", "city")
    op.drop_column("participant_profiles", "address_line1")
