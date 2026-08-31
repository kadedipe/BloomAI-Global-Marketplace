from alembic import op
import sqlalchemy as sa

revision = "0006_notification_preferences"
down_revision = "0005_notifications"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("account_in_app", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("orders_in_app", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("payments_in_app", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("vendor_activity_in_app", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("system_in_app", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("email_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_notification_preferences_user_id", "notification_preferences", ["user_id"], unique=True)


def downgrade():
    op.drop_index("ix_notification_preferences_user_id", table_name="notification_preferences")
    op.drop_table("notification_preferences")
