"""Add persistent support cases and conversations.

Revision ID: 0011_support_cases
Revises: 0010_commerce_hardening
"""

from alembic import op
import sqlalchemy as sa

revision = "0011_support_cases"
down_revision = "0010_commerce_hardening"
branch_labels = None
depends_on = None

support_case_status = sa.Enum(
    "open", "in_progress", "waiting_on_user", "resolved", "closed",
    name="supportcasestatus",
)
support_case_priority = sa.Enum(
    "normal", "high", "critical", name="supportcasepriority"
)


def upgrade() -> None:
    bind = op.get_bind()
    support_case_status.create(bind, checkfirst=True)
    support_case_priority.create(bind, checkfirst=True)
    op.create_table(
        "support_cases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("category", sa.String(length=64), nullable=False, server_default="general"),
        sa.Column("subject", sa.String(length=180), nullable=False),
        sa.Column("status", support_case_status, nullable=False, server_default="open"),
        sa.Column("priority", support_case_priority, nullable=False, server_default="normal"),
        sa.Column("assigned_admin_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_support_cases_user_id", "support_cases", ["user_id"])
    op.create_index("ix_support_cases_order_id", "support_cases", ["order_id"])
    op.create_index("ix_support_cases_category", "support_cases", ["category"])
    op.create_index("ix_support_cases_status", "support_cases", ["status"])
    op.create_index("ix_support_cases_priority", "support_cases", ["priority"])
    op.create_index("ix_support_cases_assigned_admin_id", "support_cases", ["assigned_admin_id"])
    op.create_index("ix_support_cases_last_message_at", "support_cases", ["last_message_at"])
    op.create_index("ix_support_cases_created_at", "support_cases", ["created_at"])

    op.create_table(
        "support_case_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("support_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("author_role", sa.String(length=32), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_support_case_messages_case_id", "support_case_messages", ["case_id"])
    op.create_index("ix_support_case_messages_author_user_id", "support_case_messages", ["author_user_id"])
    op.create_index("ix_support_case_messages_created_at", "support_case_messages", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_support_case_messages_created_at", table_name="support_case_messages")
    op.drop_index("ix_support_case_messages_author_user_id", table_name="support_case_messages")
    op.drop_index("ix_support_case_messages_case_id", table_name="support_case_messages")
    op.drop_table("support_case_messages")
    op.drop_index("ix_support_cases_created_at", table_name="support_cases")
    op.drop_index("ix_support_cases_last_message_at", table_name="support_cases")
    op.drop_index("ix_support_cases_assigned_admin_id", table_name="support_cases")
    op.drop_index("ix_support_cases_priority", table_name="support_cases")
    op.drop_index("ix_support_cases_status", table_name="support_cases")
    op.drop_index("ix_support_cases_category", table_name="support_cases")
    op.drop_index("ix_support_cases_order_id", table_name="support_cases")
    op.drop_index("ix_support_cases_user_id", table_name="support_cases")
    op.drop_table("support_cases")
    bind = op.get_bind()
    support_case_priority.drop(bind, checkfirst=True)
    support_case_status.drop(bind, checkfirst=True)
