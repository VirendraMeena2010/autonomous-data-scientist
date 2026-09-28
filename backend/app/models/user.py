from __future__ import annotations

from datetime import datetime
from typing import Any, TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    BigInteger,
    Index,
    JSON,
    String,
    text as sql_text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.services.ids import new_id

# Import related entities strictly for Pylance/IDE type checks
if TYPE_CHECKING:
    from app.models.analysis import Analysis, Dataset,Project


def utc_now() -> datetime:
    return datetime.now().astimezone()


class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        Index("ix_users_email", "email"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=new_id,
    )

    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        unique=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=sql_text("true"),
    )

    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=sql_text("false"),
    )

    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=sql_text("CURRENT_TIMESTAMP"),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=sql_text("CURRENT_TIMESTAMP"),
        onupdate=utc_now,
    )

    projects: Mapped[list["Project"]] = relationship(
        back_populates="owner",
    )

    datasets: Mapped[list["Dataset"]] = relationship(
        back_populates="owner",
    )

    analyses: Mapped[list["Analysis"]] = relationship(
        back_populates="owner",
    )
    storage_quota_bytes: Mapped[int] = mapped_column(
    BigInteger,
    nullable=False,
    default=10 * 1024 * 1024 * 1024,
    server_default=sql_text("10737418240"),
)

storage_used_bytes: Mapped[int] = mapped_column(
    BigInteger,
    nullable=False,
    default=0,
    server_default=sql_text("0"),
)

