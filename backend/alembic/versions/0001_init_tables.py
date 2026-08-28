"""init core tables

Revision ID: 0001_init
Revises:
Create Date: 2026-08-25
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(64), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("version", sa.String(16), nullable=False, server_default="local"),
        sa.Column("credits_balance", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    # user_llm_configs
    op.create_table(
        "user_llm_configs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("format", sa.String(32), nullable=False),
        sa.Column("base_url", sa.String(512)),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("api_key_enc", sa.String(512)),
        sa.Column("temperature", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column("max_tokens", sa.Integer(), nullable=False, server_default="8192"),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_user_llm_configs_id", "user_llm_configs", ["id"])
    op.create_index("ix_user_llm_configs_user_id", "user_llm_configs", ["user_id"])

    # credits_ledger
    op.create_table(
        "credits_ledger",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(64), nullable=False),
        sa.Column("model", sa.String(128)),
        sa.Column("in_tokens", sa.Integer()),
        sa.Column("out_tokens", sa.Integer()),
        sa.Column("ref_msg_id", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_credits_ledger_id", "credits_ledger", ["id"])
    op.create_index("ix_credits_ledger_user_id", "credits_ledger", ["user_id"])

    # messages
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("thread_id", sa.String(64), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("model", sa.String(128)),
        sa.Column("in_tokens", sa.Integer()),
        sa.Column("out_tokens", sa.Integer()),
        sa.Column("credits_cost", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("feedback", sa.String(16)),
        sa.Column("share_token", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_messages_id", "messages", ["id"])
    op.create_index("ix_messages_user_id", "messages", ["user_id"])
    op.create_index("ix_messages_thread_id", "messages", ["thread_id"])
    op.create_index("ix_messages_share_token", "messages", ["share_token"])

    # books
    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("intro", sa.Text()),
        sa.Column("genre", sa.String(64), nullable=False),
        sa.Column("platforms", sa.Text()),
        sa.Column("cover_url", sa.String(512)),
        sa.Column("target_chapters", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("target_words", sa.Integer(), nullable=False, server_default="60000"),
        sa.Column("per_chapter_words", sa.Integer(), nullable=False, server_default="3000"),
        sa.Column("protagonist_name", sa.String(64)),
        sa.Column("protagonist_intro", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_books_id", "books", ["id"])
    op.create_index("ix_books_user_id", "books", ["user_id"])

    # volumes
    op.create_table(
        "volumes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("book_id", sa.Integer(), sa.ForeignKey("books.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("sort", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_volumes_id", "volumes", ["id"])
    op.create_index("ix_volumes_book_id", "volumes", ["book_id"])

    # chapters
    op.create_table(
        "chapters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("book_id", sa.Integer(), sa.ForeignKey("books.id"), nullable=False),
        sa.Column("volume_id", sa.Integer(), sa.ForeignKey("volumes.id")),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rag_status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_chapters_id", "chapters", ["id"])
    op.create_index("ix_chapters_book_id", "chapters", ["book_id"])
    op.create_index("ix_chapters_volume_id", "chapters", ["volume_id"])


def downgrade():
    op.drop_table("chapters")
    op.drop_table("volumes")
    op.drop_table("books")
    op.drop_table("messages")
    op.drop_table("credits_ledger")
    op.drop_table("user_llm_configs")
    op.drop_table("users")
