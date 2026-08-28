"""add rag tables (chunks/entities/relations)

Revision ID: 0003_rag
Revises: 0002_mem
Create Date: 2026-08-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0003_rag"
down_revision = "0002_mem"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "rag_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("book_id", sa.Integer(), sa.ForeignKey("books.id"), nullable=False),
        sa.Column("chapter_id", sa.Integer(), sa.ForeignKey("chapters.id"), nullable=False),
        sa.Column("volume_id", sa.Integer(), sa.ForeignKey("volumes.id"), nullable=True),
        sa.Column("chunk_idx", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", JSONB, nullable=True),
        sa.Column("metadata_json", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_rag_chunks_id", "rag_chunks", ["id"])
    op.create_index("ix_rag_chunks_user_book", "rag_chunks", ["user_id", "book_id"])
    op.create_index("ix_rag_chunks_chapter", "rag_chunks", ["chapter_id"])

    op.create_table(
        "rag_entities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("book_id", sa.Integer(), sa.ForeignKey("books.id"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("chapter_id", sa.Integer(), sa.ForeignKey("chapters.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_rag_entities_id", "rag_entities", ["id"])
    op.create_index("ix_rag_entities_user_book", "rag_entities", ["user_id", "book_id"])

    op.create_table(
        "rag_relations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("book_id", sa.Integer(), sa.ForeignKey("books.id"), nullable=False),
        sa.Column("from_entity_id", sa.Integer(), sa.ForeignKey("rag_entities.id"), nullable=False),
        sa.Column("to_entity_id", sa.Integer(), sa.ForeignKey("rag_entities.id"), nullable=False),
        sa.Column("relation_type", sa.String(32), nullable=False),
        sa.Column("chapter_id", sa.Integer(), sa.ForeignKey("chapters.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_rag_relations_id", "rag_relations", ["id"])
    op.create_index("ix_rag_relations_user_book", "rag_relations", ["user_id", "book_id"])


def downgrade():
    op.drop_index("ix_rag_relations_user_book", table_name="rag_relations")
    op.drop_index("ix_rag_relations_id", table_name="rag_relations")
    op.drop_table("rag_relations")
    op.drop_index("ix_rag_entities_user_book", table_name="rag_entities")
    op.drop_index("ix_rag_entities_id", table_name="rag_entities")
    op.drop_table("rag_entities")
    op.drop_index("ix_rag_chunks_chapter", table_name="rag_chunks")
    op.drop_index("ix_rag_chunks_user_book", table_name="rag_chunks")
    op.drop_index("ix_rag_chunks_id", table_name="rag_chunks")
    op.drop_table("rag_chunks")
