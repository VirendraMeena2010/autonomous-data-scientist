from __future__ import annotations

import asyncio
import json
import tempfile
from contextlib import suppress
from typing import Any

import sentry_sdk
import structlog
from redis.asyncio import Redis
from sqlalchemy import select

from app.config import settings
from app.db.session import AsyncSessionLocal
from app.graph.graph import analysis_graph
from app.metrics import (
    ACTIVE_ANALYSES,
    ANALYSIS_COMPLETED,
    ANALYSIS_DURATION,
    ANALYSIS_STARTED,
)
from app.models.analysis import Analysis, Dataset, utc_now
from app.observability.langfuse_service import LangfuseService
from app.schemas.analysis import AnalysisStatus
from app.services.analysis_queue import AnalysisQueueService
from app.services.cancellation import (
    cancellation_requested,
    clear_cancellation,
)
from app.services.storage import StorageService
from app.telemetry import init_telemetry

logger = structlog.get_logger()


class AnalysisCancelledError(RuntimeError):
    pass


class AnalysisTimeoutError(RuntimeError):
    pass


async def run_worker() -> None:
    init_telemetry()

    worker_count = max(
        1,
        settings.worker_concurrency,
    )

    queue_service = AnalysisQueueService(settings)
    await queue_service.initialize()

    recovery_task = asyncio.create_task(
        _run_stale_recovery(queue_service),
    )

    tasks = [
        asyncio.create_task(
            _consume_queue(worker_id=index)
        )
        for index in range(worker_count)
    ]

    logger.info(
        "analysis_worker_started",
        worker_count=worker_count,
    )

    try:
        await asyncio.gather(
            recovery_task,
            *tasks,
        )

    finally:
        recovery_task.cancel()

        for task in tasks:
            task.cancel()

        await asyncio.gather(
            recovery_task,
            *tasks,
            return_exceptions=True,
        )

        await queue_service.close()


async def _run_stale_recovery(
    queue_service: AnalysisQueueService,
) -> None:
    while True:
        try:
            recovered = (
                await queue_service
                .recover_stale_running_analyses()
            )

            if recovered:
                logger.info(
                    "stale_analyses_recovered",
                    count=recovered,
                )

        except Exception:
            logger.exception(
                "stale_analysis_recovery_failed"
            )

        await asyncio.sleep(60)


async def _consume_queue(
    worker_id: int,
) -> None:
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

                await process_analysis_job(
                    payload,
                    redis,
                )

            except Exception:
                logger.exception(
                    "analysis_job_failed",
                    worker_id=worker_id,
                    payload=raw_payload,
                )

                with suppress(Exception):
                    await redis.rpush(
                        f"{settings.background_queue_name}:dead_letter",
                        json.dumps(
                            {
                                "event": (
                                    "analysis.dead_letter"
                                ),
                                "payload": (
                                    payload
                                    if "payload" in locals()
                                    else raw_payload
                                ),
                                "error": "analysis_job_failed",
                            },
                            default=str,
                        ),
                    )

    finally:
        await redis.aclose()


async def process_analysis_job(
    payload: dict[str, Any],
    redis: Redis,
) -> None:
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag(
            "analysis_id",
            str(payload.get("analysis_id")),
        )

        scope.set_context(
            "job_payload",
            payload,
        )

    try:
        await _process_analysis_job(
            payload,
            redis,
        )

    except Exception as exc:
        sentry_sdk.capture_exception(exc)
        raise


async def _process_analysis_job(
    payload: dict[str, Any],
    redis: Redis,
) -> None:
    analysis_id = str(
        payload["analysis_id"]
    )

    is_analysis_active = False

    def record_completion(
        completed_analysis: Analysis,
    ) -> None:
        nonlocal is_analysis_active

        if not is_analysis_active:
            return

        ANALYSIS_COMPLETED.labels(
            status=completed_analysis.status,
        ).inc()

        ANALYSIS_DURATION.labels(
            status=completed_analysis.status,
        ).observe(
            max(
                0.0,
                (
                    completed_analysis.finished_at
                    - completed_analysis.started_at
                ).total_seconds()
                if (
                    completed_analysis.finished_at
                    and completed_analysis.started_at
                )
                else 0.0,
            )
        )

        ACTIVE_ANALYSES.dec()
        is_analysis_active = False

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Analysis).where(
                Analysis.id == analysis_id
            )
        )

        analysis = result.scalar_one_or_none()

        if analysis is None:
            logger.warning(
                "analysis_not_found",
                analysis_id=analysis_id,
            )
            return

        if await cancellation_requested(
            redis,
            analysis_id,
        ):
            analysis.status = (
                AnalysisStatus.CANCELLED.value
            )

            analysis.error_message = (
                "cancelled_by_user"
            )

            analysis.finished_at = utc_now()

            await session.commit()
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
            select(Dataset).where(
                Dataset.id == analysis.dataset_id
            )
        )

        dataset = dataset_result.scalar_one_or_none()

        if dataset is None:
            analysis.status = (
                AnalysisStatus.FAILED.value
            )

            analysis.error_message = (
                "dataset_not_found"
            )

            analysis.finished_at = utc_now()

            await session.commit()
            return

        analysis.status = (
            AnalysisStatus.RUNNING.value
        )

        analysis.attempt = (
            analysis.attempt or 0
        ) + 1

        analysis.started_at = utc_now()
        analysis.error_message = None

        await session.commit()

        ANALYSIS_STARTED.labels(
            project_id=analysis.project_id,
            dataset_id=analysis.dataset_id,
        ).inc()

        ACTIVE_ANALYSES.inc()
        is_analysis_active = True

    langfuse = LangfuseService(settings)

    storage = StorageService(settings)

    trace_id: str | None = None

    try:
        await storage.initialize()

        with langfuse.trace_context(
            name="autonomous_analysis",
            analysis_id=analysis_id,
            metadata={
                "analysis_id": analysis_id,
                "project_id": str(
                    analysis.project_id
                ),
                "dataset_id": str(
                    analysis.dataset_id
                ),
            },
        ) as trace:

            if trace is not None:
                trace_id = trace.trace_id

            langfuse_callbacks = (
                langfuse.callbacks()
            )

            with tempfile.TemporaryDirectory(
                prefix="ads-analysis-"
            ) as temp_dir:

                dataset_path = (
                    await _resolve_dataset_path(
                        storage,
                        dataset,
                        temp_dir,
                    )
                )

                state = {
                    "analysis_id": analysis.id,
                    "project_id": analysis.project_id,
                    "dataset_id": analysis.dataset_id,
                    "question": analysis.question,
                    "dataset_path": str(
                        dataset_path
                    ),
                    "dataset_metadata": (
                        dataset.metadata_ or {}
                    ),
                    "analysis_results": [],
                    "errors": [],
                    "langfuse_trace_id": trace_id,
                    "langfuse_callbacks": (
                        langfuse_callbacks
                    ),
                }

                graph_result = await asyncio.wait_for(
                    _run_graph_with_cancellation(
                        state,
                        analysis_id,
                        redis,
                    ),
                    timeout=(
                        settings
                        .analysis_timeout_seconds
                    ),
                )

                if await cancellation_requested(
                    redis,
                    analysis_id,
                ):
                    raise AnalysisCancelledError(
                        "analysis_cancelled"
                    )

            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Analysis).where(
                        Analysis.id == analysis_id
                    )
                )

                analysis = (
                    result.scalar_one_or_none()
                )

                if analysis is None:
                    return

                input_guardrail = (
                    graph_result.get(
                        "guardrail"
                    )
                    or {}
                )

                output_guardrail = (
                    graph_result.get(
                        "report_guardrail"
                    )
                    or {}
                )

                blocked = (
                    not input_guardrail.get(
                        "allowed",
                        True,
                    )
                    or not output_guardrail.get(
                        "allowed",
                        True,
                    )
                )

                analysis.plan = (
                    graph_result.get("plan")
                )

                analysis.profile = (
                    graph_result.get("profile")
                )

                analysis.quality = (
                    graph_result.get("quality")
                )

                analysis.findings = (
                    graph_result.get("findings")
                )

                analysis.report = (
                    graph_result.get("report")
                )

                analysis.guardrail = {
                    "input": input_guardrail,
                    "output": output_guardrail,
                }

                analysis.langfuse_trace_id = (
                    trace_id
                )

                if blocked:
                    analysis.status = (
                        AnalysisStatus
                        .GUARDRAIL_BLOCKED
                        .value
                    )
                else:
                    analysis.status = (
                        AnalysisStatus
                        .SUCCEEDED
                        .value
                    )

                analysis.error_message = None
                analysis.finished_at = utc_now()

                await session.commit()

                record_completion(analysis)

                logger.info(
                    "analysis_completed",
                    analysis_id=analysis_id,
                    status=analysis.status,
                    langfuse_trace_id=trace_id,
                )

    except asyncio.TimeoutError:
        logger.exception(
            "analysis_timeout",
            analysis_id=analysis_id,
        )

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Analysis).where(
                    Analysis.id == analysis_id
                )
            )

            analysis = (
                result.scalar_one_or_none()
            )

            if analysis is not None:
                next_attempt = (
                    analysis.attempt or 0
                ) + 1

                if next_attempt >= 3:
                    analysis.status = (
                        AnalysisStatus
                        .FAILED
                        .value
                    )

                    analysis.error_message = (
                        "analysis_timeout_after_max_retries"
                    )

                else:
                    analysis.status = (
                        AnalysisStatus
                        .QUEUED
                        .value
                    )

                    analysis.error_message = (
                        "analysis_requeued_after_timeout"
                    )

                    analysis.started_at = None

                await session.commit()

                record_completion(analysis)

                queue_service = (
                    AnalysisQueueService(
                        settings
                    )
                )

                try:
                    await queue_service.enqueue_analysis(
                        analysis_id=analysis.id,
                        project_id=analysis.project_id,
                        dataset_id=analysis.dataset_id,
                        question=analysis.question,
                        attempt=next_attempt,
                    )

                finally:
                    await queue_service.close()

                return

    except AnalysisCancelledError:
        logger.info(
            "analysis_cancelled",
            analysis_id=analysis_id,
        )

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Analysis).where(
                    Analysis.id == analysis_id
                )
            )

            analysis = (
                result.scalar_one_or_none()
            )

            if analysis is not None:
                analysis.status = (
                    AnalysisStatus
                    .CANCELLED
                    .value
                )

                analysis.error_message = (
                    "cancelled_by_user"
                )

                analysis.finished_at = utc_now()

                await session.commit()

                record_completion(analysis)

    except Exception as exc:
        logger.exception(
            "analysis_execution_failed",
            analysis_id=analysis_id,
            error=str(exc),
            langfuse_trace_id=trace_id,
        )

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Analysis).where(
                    Analysis.id == analysis_id
                )
            )

            analysis = (
                result.scalar_one_or_none()
            )

            if analysis is not None:
                analysis.status = (
                    AnalysisStatus
                    .FAILED
                    .value
                )

                analysis.error_message = str(exc)
                analysis.finished_at = utc_now()

                await session.commit()

                record_completion(analysis)

        queue_service = AnalysisQueueService(
            settings
        )

        try:
            await queue_service.enqueue_dead_letter(
                payload,
                str(exc),
            )

        finally:
            await queue_service.close()

    finally:
        if is_analysis_active:
            ACTIVE_ANALYSES.dec()
            is_analysis_active = False

        try:
            await clear_cancellation(
                redis,
                analysis_id,
            )

        except Exception:
            pass

        langfuse.flush()

        storage.close()


async def _run_graph_with_cancellation(
    state: dict[str, Any],
    analysis_id: str,
    redis: Redis,
) -> dict[str, Any]:

    langfuse_callbacks = state.get(
        "langfuse_callbacks",
        [],
    )

    graph_task = asyncio.create_task(
        analysis_graph.ainvoke(
            state,
            config={
                "recursion_limit": 50,
                "callbacks": langfuse_callbacks,
                "run_name": "autonomous_analysis",
                "metadata": {
                    "langfuse_trace_id": (
                        state.get(
                            "langfuse_trace_id"
                        )
                    ),
                    "analysis_id": analysis_id,
                },
            },
        )
    )

    cancel_task = asyncio.create_task(
        _wait_for_cancellation(
            redis,
            analysis_id,
        )
    )

    try:
        done, _ = await asyncio.wait(
            {
                graph_task,
                cancel_task,
            },
            return_when=asyncio.FIRST_COMPLETED,
        )

        if (
            cancel_task in done
            and not graph_task.done()
        ):
            graph_task.cancel()

            await asyncio.gather(
                graph_task,
                return_exceptions=True,
            )

            raise AnalysisCancelledError(
                "analysis_cancelled"
            )

        if graph_task in done:
            return graph_task.result()

        raise RuntimeError(
            "analysis_graph_did_not_complete"
        )

    finally:
        for task in (
            graph_task,
            cancel_task,
        ):
            if not task.done():
                task.cancel()

        await asyncio.gather(
            graph_task,
            cancel_task,
            return_exceptions=True,
        )


async def _wait_for_cancellation(
    redis: Redis,
    analysis_id: str,
) -> None:
    while True:
        if await cancellation_requested(
            redis,
            analysis_id,
        ):
            return

        await asyncio.sleep(1)


async def _resolve_dataset_path(
    storage: StorageService,
    dataset: Dataset,
    temp_dir: str,
):
    if settings.storage_backend == "local":
        return storage.local_path(
            dataset.stored_path
        )

    from pathlib import Path

    target = (
        Path(temp_dir)
        / Path(
            dataset.original_filename
        ).name
    )

    await storage.download_file(
        dataset.stored_path,
        target,
    )

    return target


if __name__ == "__main__":
    asyncio.run(run_worker())