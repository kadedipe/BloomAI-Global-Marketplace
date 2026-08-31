"""Add participant segmentation profiles for admin reporting."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_participant_segmentation"
down_revision = "0002_product_media_orders"
branch_labels = None
depends_on = None


def upgrade() -> None:
    organization_size = postgresql.ENUM(
        "individual",
        "micro",
        "small",
        "mid_size",
        "large",
        "enterprise",
        "unclassified",
        name="organizationsize",
        create_type=False,
    )
    participant_category = postgresql.ENUM(
        "individual_consumer",
        "hobbyist_collector",
        "florist_landscaper",
        "professional_grower",
        "botanical_garden",
        "nursery_garden_center",
        "farm_agriculture_business",
        "small_business",
        "mid_size_business",
        "large_enterprise",
        "government_agency",
        "university",
        "research_institution",
        "nonprofit_ngo",
        "conservation_organization",
        "other",
        "unclassified",
        name="participantcategory",
        create_type=False,
    )
    organization_size.create(op.get_bind(), checkfirst=True)
    participant_category.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "participant_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("organization_name", sa.String(180), nullable=True),
        sa.Column("organization_size", organization_size, nullable=False),
        sa.Column("category", participant_category, nullable=False),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("industry", sa.String(120), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", name="uq_participant_profiles_user_id"),
    )
    op.create_index("ix_participant_profiles_user_id", "participant_profiles", ["user_id"], unique=True)
    op.create_index("ix_participant_profiles_organization_size", "participant_profiles", ["organization_size"])
    op.create_index("ix_participant_profiles_category", "participant_profiles", ["category"])
    op.create_index("ix_participant_profiles_country", "participant_profiles", ["country"])
    op.create_index("ix_participant_profiles_industry", "participant_profiles", ["industry"])


def downgrade() -> None:
    op.drop_table("participant_profiles")
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TYPE IF EXISTS participantcategory")
        op.execute("DROP TYPE IF EXISTS organizationsize")
