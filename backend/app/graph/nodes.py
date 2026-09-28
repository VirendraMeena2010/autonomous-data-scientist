from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import select

from app.config import settings
from app.graph.schemas import (
    AnalysisPlan,
    FindingsOutput,
    ReportOutput,
)
from app.llm import get_chat_model
from app.models.analysis import Dataset
from app.services.storage import StorageService, StorageError
from app.tools.dataset_tools import (
    assess_quality,
    execute_analysis_plan,
    profile_dataset,
)
from guardrails.nemo_service import NeMoGuardrailsService


guardrails_service = NeMoGuardrailsService(settings)


async def initial_guardrail_node(
    state: dict[str, Any],
) -> dict[str, Any]:
    result = await guardrails_service.check(
        state["question"],
        stage="input",
    )

    return {
        "guardrail": _json_safe(result),
    }


async def load_dataset_node(
    state: dict[str, Any],
) -> dict[str, Any]:
    """
    Resolve the dataset database record and make the actual dataset
    available as a local filesystem file for the analysis tools.

    The database stores the object-storage key in `stored_path`.
    The analysis tools require a local Path.
    """

    dataset_id = state.get("dataset_id")

    if not dataset_id:
        raise RuntimeError("dataset_id_missing")

    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Dataset).where(
                Dataset.id == str(dataset_id)
            )
        )

        dataset = result.scalar_one_or_none()

        if dataset is None:
            raise RuntimeError("dataset_not_found")

        stored_path = getattr(
            dataset,
            "stored_path",
            None,
        )

        if not stored_path:
            raise RuntimeError(
                "dataset_storage_path_missing"
            )

        # IMPORTANT:
        #
        # Do NOT use dataset.metadata.
        #
        # SQLAlchemy reserves `metadata`, which can resolve to
        # sqlalchemy.schema.MetaData.
        #
        # Your Dataset model exposes the JSON column as
        # `dataset_metadata`.

        dataset_metadata = getattr(
            dataset,
            "dataset_metadata",
            None,
        ) or {}

        if not isinstance(dataset_metadata, dict):
            dataset_metadata = {}

        original_filename = getattr(
            dataset,
            "original_filename",
            None,
        ) or "dataset.csv"

        media_type = getattr(
            dataset,
            "media_type",
            None,
        )

        size_bytes = getattr(
            dataset,
            "size_bytes",
            None,
        )

        row_count = getattr(
            dataset,
            "row_count",
            None,
        )

        column_count = getattr(
            dataset,
            "column_count",
            None,
        )

        status = getattr(
            dataset,
            "status",
            None,
        )

    # ---------------------------------------------------------
    # Build only JSON-safe metadata.
    # ---------------------------------------------------------

    safe_metadata: dict[str, Any] = {
        "filename": original_filename,
        "original_filename": original_filename,
        "media_type": media_type,
        "size_bytes": size_bytes,
        "row_count": row_count,
        "column_count": column_count,
        "status": status,
        "metadata": _json_safe(dataset_metadata),
    }

    # ---------------------------------------------------------
    # Download object-storage file to a temporary local file.
    # ---------------------------------------------------------

    temp_dir = Path(
        tempfile.mkdtemp(
            prefix=f"analysis_{dataset_id}_"
        )
    )

    local_path = temp_dir / original_filename

    try:
        storage = StorageService(settings)

        await storage.download_file(
            stored_path,
            local_path,
        )

        storage.close()

    except Exception:
        try:
            if temp_dir.exists():
                import shutil

                shutil.rmtree(
                    temp_dir,
                    ignore_errors=True,
                )
        except Exception:
            pass

        raise

    if not local_path.is_file():
        raise RuntimeError(
            f"dataset_file_not_found:{local_path}"
        )

    return {
        "dataset_path": str(local_path),
        "dataset_metadata": safe_metadata,
        "working_directory": str(temp_dir),
    }


async def plan_node(
    state: dict[str, Any],
) -> dict[str, Any]:
    model = get_chat_model()

    messages = [
        SystemMessage(
            content=(
                "You are a careful autonomous data scientist. "
                "Create a safe analysis plan using only supported "
                "tools: summary, missingness, distribution, "
                "correlation, group_summary, trend. "
                "Only reference columns that exist in the supplied "
                "dataset metadata."
            )
        ),
        HumanMessage(
            content=json.dumps(
                {
                    "question": state["question"],
                    "dataset_metadata": _json_safe(
                        state.get(
                            "dataset_metadata",
                            {},
                        )
                    ),
                },
                default=str,
            )
        ),
    ]

    plan = await _invoke_structured(
        model,
        AnalysisPlan,
        messages,
        state.get(
            "langfuse_callbacks",
            [],
        ),
    )

    return {
        "plan": _json_safe(
            plan.model_dump(
                mode="json",
            )
        )
    }


async def profile_node(
    state: dict[str, Any],
) -> dict[str, Any]:
    dataset_path = state.get("dataset_path")

    if not dataset_path:
        raise RuntimeError(
            "dataset_path_missing"
        )

    profile = await asyncio.to_thread(
        profile_dataset,
        Path(dataset_path),
    )

    return {
        "profile": _json_safe(profile),
    }


async def quality_node(
    state: dict[str, Any],
) -> dict[str, Any]:
    dataset_path = state.get("dataset_path")

    if not dataset_path:
        raise RuntimeError(
            "dataset_path_missing"
        )

    quality = await asyncio.to_thread(
        assess_quality,
        Path(dataset_path),
    )

    return {
        "quality": _json_safe(quality),
    }


async def analyze_node(
    state: dict[str, Any],
) -> dict[str, Any]:
    dataset_path = state.get("dataset_path")

    if not dataset_path:
        raise RuntimeError(
            "dataset_path_missing"
        )

    results = await asyncio.to_thread(
        execute_analysis_plan,
        Path(dataset_path),
        state.get("plan") or {},
    )

    return {
        "analysis_results": _json_safe(results),
    }


async def findings_node(
    state: dict[str, Any],
) -> dict[str, Any]:
    model = get_chat_model()

    messages = [
        SystemMessage(
            content=(
                "You are a skeptical senior data scientist. "
                "Return only evidence-backed findings. "
                "Do not invent facts."
            )
        ),
        HumanMessage(
            content=json.dumps(
                {
                    "question": state["question"],
                    "profile": _json_safe(
                        state.get("profile")
                    ),
                    "quality": _json_safe(
                        state.get("quality")
                    ),
                    "analysis_results": _json_safe(
                        state.get(
                            "analysis_results",
                            [],
                        )
                    ),
                },
                default=str,
            )
        ),
    ]

    findings = await _invoke_structured(
        model,
        FindingsOutput,
        messages,
        state.get(
            "langfuse_callbacks",
            [],
        ),
    )

    findings_data = findings.model_dump(
        mode="json"
    )

    return {
        "findings": _json_safe(
            findings_data.get(
                "findings",
                [],
            )
        )
    }


async def report_node(
    state: dict[str, Any],
) -> dict[str, Any]:
    model = get_chat_model()

    messages = [
        SystemMessage(
            content=(
                "You write concise analytical reports. "
                "Use evidence only. Include caveats and next steps."
            )
        ),
        HumanMessage(
            content=json.dumps(
                {
                    "question": state["question"],
                    "findings": _json_safe(
                        state.get(
                            "findings",
                            [],
                        )
                    ),
                    "quality": _json_safe(
                        state.get("quality")
                    ),
                    "profile": _json_safe(
                        state.get("profile")
                    ),
                },
                default=str,
            )
        ),
    ]

    report = await _invoke_structured(
        model,
        ReportOutput,
        messages,
        state.get(
            "langfuse_callbacks",
            [],
        ),
    )

    return {
        "report": _json_safe(
            report.model_dump(
                mode="json",
            )
        )
    }


async def final_guardrail_node(
    state: dict[str, Any],
) -> dict[str, Any]:
    result = await guardrails_service.check(
        json.dumps(
            state.get("report") or {},
            default=str,
        ),
        stage="output",
    )

    return {
        "report_guardrail": _json_safe(result),
    }


def route_after_input_guardrail(
    state: dict[str, Any],
) -> str:
    guardrail = state.get(
        "guardrail",
        {},
    )

    if not guardrail.get(
        "allowed",
        True,
    ):
        return "blocked"

    return "load_dataset"


def route_after_output_guardrail(
    state: dict[str, Any],
) -> str:
    guardrail = state.get(
        "report_guardrail",
        {},
    )

    if not guardrail.get(
        "allowed",
        True,
    ):
        return "blocked"

    return "end"


def blocked_node(
    state: dict[str, Any],
) -> dict[str, Any]:
    return {}


async def _invoke_structured(
    model: Any,
    schema: Any,
    messages: list[Any],
    callbacks: list[Any],
) -> Any:
    chain = await asyncio.to_thread(
        model.with_structured_output,
        schema,
    )

    return await asyncio.to_thread(
        chain.invoke,
        messages,
        {
            "callbacks": callbacks,
        },
    )


def _json_safe(value: Any) -> Any:
    """
    Convert values that may not be serializable by LangGraph's
    checkpoint serializer into JSON-safe Python values.

    In particular, this prevents SQLAlchemy MetaData, Path,
    UUID and other runtime objects from entering graph state.
    """

    if value is None:
        return None

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        return value

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            _json_safe(item)
            for item in value
        ]

    if isinstance(value, set):
        return [
            _json_safe(item)
            for item in value
        ]

    if hasattr(value, "model_dump"):
        try:
            return _json_safe(
                value.model_dump(
                    mode="json"
                )
            )
        except Exception:
            pass

    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass

    return str(value)