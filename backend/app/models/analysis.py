from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    text as sql_text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.services.ids import new_id


if TYPE_CHECKING:
    from app.models.user import User


def utc_now() -> datetime:
    return datetime.now().astimezone()


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=new_id,
    )

    owner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(1024),
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

    owner: Mapped["User"] = relationship(
        back_populates="projects",
    )

    datasets: Mapped[list["Dataset"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )

    analyses: Mapped[list["Analysis"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=new_id,
    )

    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id"),
        nullable=False,
    )

    owner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    stored_path: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )

    media_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    row_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    column_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="uploaded",
    )

    # Do not name the Python attribute "metadata".
    # SQLAlchemy reserves Base.metadata.
    dataset_metadata: Mapped[dict[str, Any] | None] = mapped_column(
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

    owner: Mapped["User"] = relationship(
        back_populates="datasets",
    )

    project: Mapped["Project"] = relationship(
        back_populates="datasets",
    )

    analyses: Mapped[list["Analysis"]] = relationship(
        back_populates="dataset",
        cascade="all, delete-orphan",
    )


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=new_id,
    )

    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id"),
        nullable=False,
    )

    owner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
    )

    dataset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("datasets.id"),
        nullable=False,
    )

    question: Mapped[str] = mapped_column(
        String(5000),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="queued",
    )

    attempt: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    plan: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    profile: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    quality: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    findings: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    report: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    guardrail: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    langfuse_trace_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        String(4000),
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
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

    owner: Mapped["User"] = relationship(
        back_populates="analyses",
    )

    project: Mapped["Project"] = relationship(
        back_populates="analyses",
    )

    dataset: Mapped["Dataset"] = relationship(
        back_populates="analyses",
    )