
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
)


class AnalysisStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    GUARDRAIL_BLOCKED = "guardrail_blocked"


class ProjectCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=4000,
    )


class ProjectRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    owner_id: UUID | None = None
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class DatasetRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    id: UUID
    project_id: UUID
    owner_id: UUID | None = None

    original_filename: str
    stored_path: str
    media_type: str
    size_bytes: int
    sha256: str

    row_count: int | None
    column_count: int | None
    status: str

    metadata: dict[str, Any] | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "dataset_metadata",
            "metadata",
            "metadata_",
        ),
        serialization_alias="metadata",
    )

    created_at: datetime
    updated_at: datetime


class AnalysisCreate(BaseModel):
    dataset_id: UUID

    question: str = Field(
        min_length=3,
        max_length=5000,
    )


class AnalysisRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    project_id: UUID
    owner_id: UUID | None = None
    dataset_id: UUID

    question: str

    # String annotation avoids Pylance confusing the enum
    # with a module having the same name.
    status: "AnalysisStatus"

    attempt: int

    plan: dict[str, Any] | None = None
    profile: dict[str, Any] | None = None
    quality: dict[str, Any] | None = None

    findings: list[dict[str, Any]] | None = None

    report: dict[str, Any] | None = None
    guardrail: dict[str, Any] | None = None

    langfuse_trace_id: str | None = None
    error_message: str | None = None

    started_at: datetime | None = None
    finished_at: datetime | None = None

    created_at: datetime
    updated_at: datetime


class ProjectSummary(BaseModel):
    project_id: str
    dataset_count: int
    analysis_count: int
    succeeded_count: int
    failed_count: int
    success_rate: float

