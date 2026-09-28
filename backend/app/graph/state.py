from __future__ import annotations

from typing import Any, TypedDict


class AnalysisState(TypedDict, total=False):
    analysis_id: str
    project_id: str
    dataset_id: str
    question: str

    # Always a local filesystem path while the graph is running.
    dataset_path: str

    # JSON-safe dataset metadata only.
    dataset_metadata: dict[str, Any]

    plan: dict[str, Any] | None
    profile: dict[str, Any] | None
    quality: dict[str, Any] | None

    analysis_results: list[dict[str, Any]]

    findings: list[dict[str, Any]] | None
    report: dict[str, Any] | None

    guardrail: dict[str, Any] | None
    report_guardrail: dict[str, Any] | None

    langfuse_trace_id: str | None

    errors: list[str]

    # Internal runtime-only path.
    # Do not put Path/SQLAlchemy objects here.
    working_directory: str | None