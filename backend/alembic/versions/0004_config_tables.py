"""add config entities + entity_kv tables (P1-7)

Revision ID: 0004_cfg
Revises: 0003_rag
Create Date: 2026-08-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0004_cfg"
down_revision = "0003_rag"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "config_entities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("book_id", sa.Integer(), sa.ForeignKey("books.id"), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("category", sa.String(64), nullable=False, server_default=""),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("image_url", sa.String(512), nullable=True),
        sa.Column("extra_json", JSONB, nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("book_id", "entity_type", "name", name="uq_config_entity_name"),
    )
    op.create_index("ix_config_entities_book_id", "config_entities", ["book_id"])
    op.create_index("ix_config_entities_entity_type", "config_entities", ["entity_type"])

    op.create_table(
        "entity_kv",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("value", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("entity_type", "entity_id", "key", name="uq_entity_kv"),
    )
    op.create_index("ix_entity_kv_entity_type", "entity_kv", ["entity_type"])
    op.create_index("ix_entity_kv_entity_id", "entity_kv", ["entity_id"])


def downgrade():
    op.drop_table("entity_kv")
    op.drop_table("config_entities")
