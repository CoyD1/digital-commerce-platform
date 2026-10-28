"""add user roles

Revision ID: ef90b93979df
Revises: aca46a3efa9c
Create Date: 2026-10-29 01:49:52.991800

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ef90b93979df"
down_revision: str | Sequence[str] | None = "aca46a3efa9c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add user roles."""
    user_role = sa.Enum(
        "CUSTOMER",
        "ADMIN",
        name="user_role",
    )

    user_role.create(op.get_bind(), checkfirst=False)

    op.add_column(
        "users",
        sa.Column(
            "role",
            user_role,
            server_default="CUSTOMER",
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Remove user roles."""
    op.drop_column("users", "role")

    user_role = sa.Enum(
        "CUSTOMER",
        "ADMIN",
        name="user_role",
    )
    user_role.drop(op.get_bind(), checkfirst=False)
