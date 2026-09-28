from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import Analysis, utc_now
from app.schemas.analysis import AnalysisStatus
from app.services.analyses import get_analysis_for_project
from app.services.queue import AnalysisQueue, AnalysisQueueError


_ACTIVE_STATUSES = {
    AnalysisStatus.QUEUED.value,
    AnalysisStatus.RUNNING.value,
}

_RETRYABLE_STATUSES = {
    AnalysisStatus.FAILED.value,
    AnalysisStatus.GUARDRAIL_BLOCKED.value,
    AnalysisStatus.CANCELLED.value,
}

_CANCELABLE_STATUSES = {
    AnalysisStatus.QUEUED.value,
    AnalysisStatus.RUNNING.value,
}


async def retry_analysis(
    session: AsyncSession,
    project_id: UUID | str,
    analysis_id: UUID | str,
    queue: AnalysisQueue,
) -> Analysis:
    analysis = await get_analysis_for_project(
        session,
        project_id,
        analysis_id,
    )

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="analysis_not_found",
        )

    if analysis.status in _ACTIVE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="analysis_already_active",
        )

    if analysis.status not in _RETRYABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="analysis_not_retryable",
        )

    analysis.attempt = (analysis.attempt or 0) + 1
    analysis.status = AnalysisStatus.QUEUED.value
    analysis.started_at = None
    analysis.finished_at = None
    analysis.error_message = None
    analysis.langfuse_trace_id = None

    analysis.plan = None
    analysis.profile = None
    analysis.quality = None
    analysis.findings = None
    analysis.report = None
    analysis.guardrail = None

    await session.commit()
    await session.refresh(analysis)

    try:
        await queue.enqueue_analysis(
            analysis_id=analysis.id,
            project_id=analysis.project_id,
            dataset_id=analysis.dataset_id,
            question=analysis.question,
            attempt=analysis.attempt,
        )
    except AnalysisQueueError as exc:
        analysis.status = AnalysisStatus.FAILED.value
        analysis.error_message = "analysis_queue_unavailable"
        analysis.finished_at = utc_now()
        await session.commit()

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="analysis_queue_unavailable",
        ) from exc

    return analysis


async def cancel_analysis(
    session: AsyncSession,
    project_id: UUID | str,
    analysis_id: UUID | str,
) -> Analysis:
    analysis = await get_analysis_for_project(
        session,
        project_id,
        analysis_id,
    )

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="analysis_not_found",
        )

    if analysis.status not in _CANCELABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="analysis_not_cancelable",
        )

    analysis.status = AnalysisStatus.CANCELLED.value
    analysis.error_message = "cancelled_by_user"
    analysis.finished_at = utc_now()

    await session.commit()
    await session.refresh(analysis)

    return analysis
