"""add collections

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-20
"""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "collections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "collection_recipes",
        sa.Column("collection_id", sa.Integer(), sa.ForeignKey("collections.id"), primary_key=True),
        sa.Column("recipe_id", sa.Integer(), sa.ForeignKey("recipes.id"), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("collection_recipes")
    op.drop_table("collections")
