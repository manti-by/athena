"""Add source column to images table

Revision ID: 003
Revises: 002
Create Date: 2026-03-16

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "003"
down_revision: str | Sequence[str] | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE TYPE imagesource AS ENUM ('USER', 'OPENROUTER')")
    op.add_column(
        "images",
        sa.Column(
            "source",
            sa.Enum("USER", "OPENROUTER", name="imagesource", createtype=False),
            nullable=False,
            server_default="USER",
        ),
    )


def downgrade() -> None:
    op.drop_column("images", "source")
    sa.Enum(name="imagesource").drop(op.get_bind(), checkfirst=True)
