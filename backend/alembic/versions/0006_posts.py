"""add posts + post_book_links tables (P1-9)

Revision ID: 0006_post
Revises: 0005_read
Create Date: 2026-08-25
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_post"
down_revision = "0005_read"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "posts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content_html", sa.Text(), nullable=False, server_default=""),
        sa.Column("content_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_posts_user_id", "posts", ["user_id"])

    op.create_table(
        "post_book_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("post_id", sa.Integer(), sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("book_id", sa.Integer(), sa.ForeignKey("books.id"), nullable=False),
    )
    op.create_index("ix_post_book_links_post_id", "post_book_links", ["post_id"])
    op.create_index("ix_post_book_links_book_id", "post_book_links", ["book_id"])


def downgrade():
    op.drop_table("post_book_links")
    op.drop_table("posts")
