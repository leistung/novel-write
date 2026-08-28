"""add is_admin to users + social tables (P2-10)

Revision ID: 0007_adm
Revises: 0006_post
Create Date: 2026-08-26
"""
from alembic import op
import sqlalchemy as sa


revision = "0007_adm"
down_revision = "0006_post"
branch_labels = None
depends_on = None


def upgrade():
    # users 加 is_admin 列
    op.add_column("users", sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()))

    # friendships 表
    op.create_table(
        "friendships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("friend_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_friendships_user_id", "friendships", ["user_id"])
    op.create_index("ix_friendships_friend_id", "friendships", ["friend_id"])

    # social_messages 表
    op.create_table(
        "social_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sender_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("receiver_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("msg_type", sa.String(16), nullable=False, server_default="text"),
        sa.Column("attachment_url", sa.String(512), nullable=True),
        sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_social_messages_sender_id", "social_messages", ["sender_id"])
    op.create_index("ix_social_messages_receiver_id", "social_messages", ["receiver_id"])


def downgrade():
    op.drop_table("social_messages")
    op.drop_table("friendships")
    op.drop_column("users", "is_admin")
