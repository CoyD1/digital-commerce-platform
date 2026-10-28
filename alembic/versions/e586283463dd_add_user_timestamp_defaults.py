"""add user timestamp defaults

Revision ID: e586283463dd
Revises: a4097998370d
Create Date: 2026-10-22 01:36:40.796553

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e586283463dd"
down_revision: str | Sequence[str] | None = "a4097998370d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "users",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        existing_nullable=False,
    )

    op.alter_column(
        "users",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "users",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        existing_nullable=False,
    )

    op.alter_column(
        "users",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        existing_nullable=False,
    )
