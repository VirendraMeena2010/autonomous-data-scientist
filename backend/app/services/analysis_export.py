from __future__ import annotations

import json

from fastapi.encoders import jsonable_encoder

from app.models.analysis import Analysis


def render_analysis_export(
    analysis: Analysis,
    export_format: str,
) -> tuple[str, str, str]:
    data = {
        "id": analysis.id,
        "project_id": analysis.project_id,
        "dataset_id": analysis.dataset_id,
        "question": analysis.question,
        "status": analysis.status,
        "attempt": analysis.attempt,
        "plan": analysis.plan,
        "profile": analysis.profile,
        "quality": analysis.quality,
        "findings": analysis.findings,
        "report": analysis.report,
        "guardrail": analysis.guardrail,
        "langfuse_trace_id": analysis.langfuse_trace_id,
        "error_message": analysis.error_message,
        "started_at": analysis.started_at,
        "finished_at": analysis.finished_at,
        "created_at": analysis.created_at,
        "updated_at": analysis.updated_at,
    }

    encoded = jsonable_encoder(data)
    safe_id = _safe_filename(analysis.id)

    if export_format == "json":
        return (
            json.dumps(encoded, indent=2, ensure_ascii=False),
            "application/json",
            f"analysis-{safe_id}.json",
        )

    if export_format == "markdown":
        return (
            _render_markdown(encoded),
            "text/markdown",
            f"analysis-{safe_id}.md",
        )

    raise ValueError(f"unsupported_export_format:{export_format}")


def _safe_filename(value: str) -> str:
    safe = "".join(
        char for char in value
        if char.isalnum() or char in {"-", "_"}
    )
    return safe or "analysis"


def _render_markdown(data: dict[str, object]) -> str:
    lines = [
        f"# {data.get('question', 'Analysis')}",
        "",
        f"**Status:** `{data.get('status', 'unknown')}`",
        "",
        f"**Attempt:** {data.get('attempt', 0)}",
        "",
    ]

    if data.get("error_message"):
        lines.extend(
            [
                "## Error",
                "",
                str(data["error_message"]),
                "",
            ]
        )

    report = data.get("report")

    if isinstance(report, dict):
        lines.extend(
            [
                f"## {report.get('title', 'Report')}",
                "",
                str(report.get("executive_summary", "")),
                "",
            ]
        )

        sections = report.get("sections", [])

        if isinstance(sections, list):
            for section in sections:
                if not isinstance(section, dict):
                    continue

                lines.extend(
                    [
                        f"### {section.get('heading', 'Section')}",
                        "",
                        str(section.get("content", "")),
                        "",
                    ]
                )

        caveats = report.get("caveats", [])

        if isinstance(caveats, list) and caveats:
            lines.extend(["## Caveats", ""])
            lines.extend(f"- {item}" for item in caveats)
            lines.append("")

        next_steps = report.get("recommended_next_steps", [])

        if isinstance(next_steps, list) and next_steps:
            lines.extend(["## Recommended next steps", ""])
            lines.extend(f"- {item}" for item in next_steps)
            lines.append("")

    findings = data.get("findings")

    if isinstance(findings, list) and findings:
        lines.extend(["## Findings", ""])

        for finding in findings:
            if not isinstance(finding, dict):
                continue

            lines.extend(
                [
                    f"- **{finding.get('title', 'Finding')}** "
                    f"({finding.get('severity', 'unknown')}, "
                    f"confidence {finding.get('confidence', 'n/a')})",
                    "",
                    str(finding.get("description", "")),
                    "",
                ]
            )

    lines.extend(
        [
            "## Raw JSON",
            "",
            "```json",
            json.dumps(data, indent=2, ensure_ascii=False),
            "```",
        ]
    )

    return "\n".join(lines).strip() + "\n"
