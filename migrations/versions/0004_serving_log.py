"""add serving log

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-20
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "serving_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("recipe_id", sa.Integer(), sa.ForeignKey("recipes.id"), nullable=False, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("served_on", sa.Date(), nullable=False),
        sa.Column("note", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("serving_log")
