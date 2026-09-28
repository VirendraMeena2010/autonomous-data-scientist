"""Add user storage quota.

Revision ID: 0004_user_storage_quota
Revises: 0003_schema_audit_fixes
Create Date: 2024-01-01 00:00:00.000000"""



from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004_user_storage_quota"
down_revision: Union[str, None] = "0003_schema_audit_fixes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "storage_quota_bytes",
            sa.BigInteger(),
            server_default=sa.text("10737418240"),
            nullable=False,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "storage_used_bytes",
            sa.BigInteger(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "storage_used_bytes")
    op.drop_column("users", "storage_quota_bytes")
