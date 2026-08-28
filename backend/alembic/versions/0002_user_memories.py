"""add user_memories table

Revision ID: 0002_mem
Revises: 0001_init
Create Date: 2026-08-25
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_mem"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_memories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("value", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_user_memories_id", "user_memories", ["id"])
    op.create_index("ix_user_memories_user_id", "user_memories", ["user_id"])


def downgrade():
    op.drop_index("ix_user_memories_user_id", table_name="user_memories")
    op.drop_index("ix_user_memories_id", table_name="user_memories")
    op.drop_table("user_memories")
