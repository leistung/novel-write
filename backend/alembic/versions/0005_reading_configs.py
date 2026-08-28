"""add reading_configs table (P1-8)

Revision ID: 0005_read
Revises: 0004_cfg
Create Date: 2026-08-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0005_read"
down_revision = "0004_cfg"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "reading_configs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("book_id", sa.Integer(), sa.ForeignKey("books.id"), nullable=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("scene", sa.String(32), nullable=False, server_default="default"),
        sa.Column("config_json", JSONB, nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_reading_configs_user_id", "reading_configs", ["user_id"])
    op.create_index("ix_reading_configs_book_id", "reading_configs", ["book_id"])


def downgrade():
    op.drop_table("reading_configs")
