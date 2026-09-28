"""Schema audit fixes.

Revision ID: 0003_schema_audit_fixes
Revises: 0002_users
Create Date: 2026-01-01 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_schema_audit_fixes"
down_revision: Union[str, None] = "0002_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("owner_id", sa.String(length=36), nullable=True),
    )

    op.add_column(
        "datasets",
        sa.Column("owner_id", sa.String(length=36), nullable=True),
    )

    op.add_column(
        "analyses",
        sa.Column("owner_id", sa.String(length=36), nullable=True),
    )

    op.create_foreign_key(
        "fk_projects_owner_id_users",
        "projects",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_foreign_key(
        "fk_datasets_owner_id_users",
        "datasets",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="SET NULL",
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
        "ix_projects_owner_id",
        "projects",
        ["owner_id"],
        unique=False,
    )

    op.create_index(
        "ix_datasets_owner_id",
        "datasets",
        ["owner_id"],
        unique=False,
    )

    op.create_index(
        "ix_analyses_owner_id",
        "analyses",
        ["owner_id"],
        unique=False,
    )

    op.alter_column(
        "users",
        "metadata",
        existing_type=sa.String(),
        type_=sa.JSON(),
        nullable=True,
        postgresql_using="to_jsonb(metadata)",
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "metadata",
        existing_type=sa.JSON(),
        type_=sa.String(),
        nullable=True,
        postgresql_using="metadata::text",
    )

    op.drop_index(
        "ix_analyses_owner_id",
        table_name="analyses",
    )

    op.drop_index(
        "ix_datasets_owner_id",
        table_name="datasets",
    )

    op.drop_index(
        "ix_projects_owner_id",
        table_name="projects",
    )

    op.drop_constraint(
        "fk_analyses_owner_id_users",
        "analyses",
        type_="foreignkey",
    )

    op.drop_constraint(
        "fk_datasets_owner_id_users",
        "datasets",
        type_="foreignkey",
    )

    op.drop_constraint(
        "fk_projects_owner_id_users",
        "projects",
        type_="foreignkey",
    )

    op.drop_column("analyses", "owner_id")
    op.drop_column("datasets", "owner_id")
    op.drop_column("projects", "owner_id")
