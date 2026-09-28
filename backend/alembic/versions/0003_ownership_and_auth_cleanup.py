"""Ownership and auth cleanup.

Revision ID: 0003_ownership_and_auth_cleanup
Revises: 0002_users
Create Date: 2026-01-01 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_ownership_and_auth_cleanup"
down_revision: Union[str, None] = "0002_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column(
            "owner_id",
            sa.String(length=36),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_projects_owner_id_users",
        "projects",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "datasets",
        sa.Column(
            "owner_id",
            sa.String(length=36),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_datasets_owner_id_users",
        "datasets",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "analyses",
        sa.Column(
            "owner_id",
            sa.String(length=36),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_analyses_owner_id_users",
        "analyses",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_index(
        "ix_projects_owner_created",
        "projects",
        ["owner_id", "created_at"],
        unique=False,
    )

    op.create_index(
        "ix_datasets_owner_created",
        "datasets",
        ["owner_id", "created_at"],
        unique=False,
    )

    op.create_index(
        "ix_analyses_owner_created",
        "analyses",
        ["owner_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_analyses_owner_created",
        table_name="analyses",
    )

    op.drop_index(
        "ix_datasets_owner_created",
        table_name="datasets",
    )

    op.drop_index(
        "ix_projects_owner_created",
        table_name="projects",
    )

    op.drop_foreign_key(
        "fk_analyses_owner_id_users",
        table_name="analyses",
    )

    op.drop_foreign_key(
        "fk_datasets_owner_id_users",
        table_name="datasets",
    )

    op.drop_foreign_key(
        "fk_projects_owner_id_users",
        table_name="projects",
    )

    op.drop_column(
        "analyses",
        "owner_id",
    )

    op.drop_column(
        "datasets",
        "owner_id",
    )

    op.drop_column(
        "projects",
        "owner_id",
    )
