from __future__ import annotations

import asyncio
import json
import tempfile
from typing import Any

import structlog
from redis.asyncio import Redis
from sqlalchemy import select

from app.config import settings
from app.db.session import AsyncSessionLocal
from app.graph.graph import analysis_graph
from app.models.analysis import Analysis, Dataset, utc_now
from app.observability.langfuse_service import LangfuseService
from app.schemas.analysis import AnalysisStatus
from app.services.storage import StorageService

logger = structlog.get_logger()


async def run_worker() -> None:
    worker_count = max(1, settings.worker_concurrency)
    tasks = [
        asyncio.create_task(_consume_queue(worker_id=index))
        for index in range(worker_count)
    ]

    logger.info("analysis_worker_started", worker_count=worker_count)

    try:
        await asyncio.gather(*tasks)
    finally:
        for task in tasks:
            task.cancel()


async def _consume_queue(*, worker_id: int) -> None:
    redis = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )

    try:
        while True:
            item = await redis.blpop(
                settings.background_queue_name,
                timeout=30,
            )

            if not item:
                continue

            _, raw_payload = item

            try:
                payload = json.loads(raw_payload)
                await process_analysis_job(payload)
            except Exception:
                logger.exception(
                    "analysis_job_failed",
                    worker_id=worker_id,
                    payload=raw_payload,
                )
    finally:
        await redis.aclose()


async def process_analysis_job(payload: dict[str, Any]) -> None:
    analysis_id = str(payload["analysis_id"])

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Analysis).where(Analysis.id == analysis_id)
        )
        analysis = result.scalar_one_or_none()

        if analysis is None:
            logger.warning("analysis_not_found", analysis_id=analysis_id)
            return

        if analysis.status in {
            AnalysisStatus.SUCCEEDED.value,
            AnalysisStatus.FAILED.value,
            AnalysisStatus.CANCELLED.value,
            AnalysisStatus.GUARDRAIL_BLOCKED.value,
        }:
            logger.info(
                "analysis_already_terminal",
                analysis_id=analysis_id,
                status=analysis.status,
            )
            return

        dataset_result = await session.execute(
            select(Dataset).where(Dataset.id == analysis.dataset_id)
        )
        dataset = dataset_result.scalar_one_or_none()

        if dataset is None:
            analysis.status = AnalysisStatus.FAILED.value
            analysis.error_message = "dataset_not_found"
            analysis.finished_at = utc_now()
            await session.commit()
            return

        analysis.status = AnalysisStatus.RUNNING.value
        analysis.attempt += 1
        analysis.started_at = utc_now()
        analysis.error_message = None
        await session.commit()

    langfuse = LangfuseService(settings)
    trace = langfuse.start_trace(
        name="autonomous_analysis",
        analysis_id=analysis_id,
        metadata={
            "project_id": analysis.project_id,
            "dataset_id": analysis.dataset_id,
        },
    )

    storage = StorageService(settings)
    await storage.initialize()

    try:
        with tempfile.TemporaryDirectory(prefix="ads-analysis-") as temp_dir:
            dataset_path = await _resolve_dataset_path(
                storage,
                dataset,
                temp_dir,
            )

            state = {
                "analysis_id": analysis.id,
                "project_id": analysis.project_id,
                "dataset_id": analysis.dataset_id,
                "question": analysis.question,
                "dataset_path": str(dataset_path),
                "dataset_metadata": dataset.metadata_ or {},
                "analysis_results": [],
                "errors": [],
                "langfuse_trace_id": trace.id if trace else None,
                "langfuse_callbacks": langfuse.callbacks(trace),
            }

            result = await analysis_graph.ainvoke(
                state,
                config={
                    "recursion_limit": 50,
                },
            )

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Analysis).where(Analysis.id == analysis_id)
            )
            analysis = result.scalar_one_or_none()

            if analysis is None:
                return

            guardrail_payload = {
                "input": result.get("guardrail"),
                "output": result.get("report_guardrail"),
            }

            blocked = (
                not result.get("guardrail", {}).get("allowed", True)
                or not result.get("report_guardrail", {}).get("allowed", True)
            )

            analysis.plan = result.get("plan")
            analysis.profile = result.get("profile")
            analysis.quality = result.get("quality")
            analysis.findings = result.get("findings")
            analysis.report = result.get("report")
            analysis.guardrail = guardrail_payload
            analysis.langfuse_trace_id = trace.id if trace else None

            if blocked:
                analysis.status = AnalysisStatus.GUARDRAIL_BLOCKED.value
            else:
                analysis.status = AnalysisStatus.SUCCEEDED.value

            analysis.finished_at = utc_now()
            await session.commit()

            logger.info(
                "analysis_completed",
                analysis_id=analysis_id,
                status=analysis.status,
            )

    except Exception as exc:
        logger.exception(
            "analysis_execution_failed",
            analysis_id=analysis_id,
            error=str(exc),
        )

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Analysis).where(Analysis.id == analysis_id)
            )
            analysis = result.scalar_one_or_none()

            if analysis is not None:
                analysis.status = AnalysisStatus.FAILED.value
                analysis.error_message = str(exc)
                analysis.finished_at = utc_now()
                await session.commit()

    finally:
        langfuse.end_trace(trace)
        langfuse.flush()
        storage.close()


async def _resolve_dataset_path(
    storage: StorageService,
    dataset: Dataset,
    temp_dir: str,
):
    if settings.storage_backend == "local":
        return storage.local_path(dataset.stored_path)

    from pathlib import Path

    target = Path(temp_dir) / Path(dataset.original_filename).name
    await storage.download_file(dataset.stored_path, target)
    return target


if __name__ == "__main__":
    asyncio.run(run_worker())
