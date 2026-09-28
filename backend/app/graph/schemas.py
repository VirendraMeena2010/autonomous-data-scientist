from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PlanParameters(StrictBaseModel):
    column: str | None = None
    columns: list[str] = Field(default_factory=list)
    group_by: str | None = None
    target: str | None = None
    time_column: str | None = None
    aggregation: (
        Literal[
            "sum",
            "mean",
            "median",
            "min",
            "max",
            "count",
            "std",
        ]
        | None
    ) = None


class PlanStep(StrictBaseModel):
    name: str = Field(min_length=1, max_length=120)
    tool: Literal[
        "summary",
        "missingness",
        "distribution",
        "correlation",
        "group_summary",
        "trend",
    ]
    parameters: PlanParameters = Field(default_factory=PlanParameters)
    rationale: str | None = None


class AnalysisPlan(StrictBaseModel):
    objective: str
    steps: list[PlanStep] = Field(min_length=1, max_length=12)
    required_columns: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)


class FindingEvidence(StrictBaseModel):
    metric: str | None = None
    value: str | float | int | None = None
    column: str | None = None
    columns: list[str] = Field(default_factory=list)
    description: str | None = None


class Finding(StrictBaseModel):
    title: str
    description: str
    severity: Literal["low", "medium", "high"]
    confidence: float = Field(ge=0, le=1)
    evidence: FindingEvidence = Field(default_factory=FindingEvidence)


class FindingsOutput(StrictBaseModel):
    findings: list[Finding] = Field(min_length=0, max_length=20)
    caveats: list[str] = Field(default_factory=list)


class ReportEvidence(StrictBaseModel):
    metric: str | None = None
    value: str | float | int | None = None
    column: str | None = None
    columns: list[str] = Field(default_factory=list)
    description: str | None = None


class ReportSection(StrictBaseModel):
    heading: str
    content: str
    evidence: ReportEvidence = Field(default_factory=ReportEvidence)


class ReportOutput(StrictBaseModel):
    title: str
    executive_summary: str
    sections: list[ReportSection] = Field(min_length=1, max_length=12)
    caveats: list[str] = Field(default_factory=list)
    recommended_next_steps: list[str] = Field(default_factory=list)