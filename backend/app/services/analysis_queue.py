from __future__ import annotations

import json
from typing import Any

from redis.asyncio import Redis

from app.config import Settings
from app.config import settings


class AnalysisQueueService:
    def __init__(self, model_settings: Settings | None = None) -> None:
        model_settings = model_settings or settings
        self.settings = model_settings
        self.redis = Redis.from_url(
            model_settings.redis_url,
            decode_responses=True,
        )

    async def ping(self) -> bool:
        return bool(await self.redis.ping())

    async def close(self) -> None:
        await self.redis.aclose()

    async def enqueue_analysis(
        self,
        *,
        analysis_id: str,
        project_id: str,
        dataset_id: str,
        question: str,
        attempt: int,
    ) -> None:
        payload = {
            "event": "analysis.requested",
            "analysis_id": analysis_id,
            "project_id": project_id,
            "dataset_id": dataset_id,
            "question": question,
            "attempt": attempt,
        }

        await self.redis.rpush(
            self.settings.background_queue_name,
            json.dumps(payload, separators=(",", ":")),
        )

    async def enqueue_dead_letter(
        self,
        payload: dict[str, Any],
        error: str,
    ) -> None:
        dead_payload = {
            **payload,
            "event": "analysis.dead_letter",
            "error": error,
        }

        await self.redis.rpush(
            f"{self.settings.background_queue_name}:dead_letter",
            json.dumps(dead_payload, separators=(",", ":"), default=str),
        )

    async def recover_stale_running_analyses(self) -> int:
        """
        Mark running jobs stale if they exceeded timeout.
        Requeue them up to max retry attempt.
        """
        from sqlalchemy import select, update

        from app.db.session import AsyncSessionLocal
        from app.models.analysis import Analysis
        from app.schemas.analysis import AnalysisStatus

        recovered = 0

        async with AsyncSessionLocal() as session:
            stale_ids = await self._get_stale_analysis_ids()

            for analysis_id in stale_ids:
                result = await session.execute(
                    select(Analysis).where(Analysis.id == analysis_id)
                )
                analysis = result.scalar_one_or_none()

                if analysis is None:
                    continue

                next_attempt = (analysis.attempt or 0) + 1

                if next_attempt > 3:
                    analysis.status = AnalysisStatus.FAILED.value
                    analysis.error_message = "analysis_timeout_after_max_retries"
                    analysis.finished_at = analysis.started_at
                    await session.commit()
                    continue

                analysis.status = AnalysisStatus.QUEUED.value
                analysis.error_message = "analysis_requeued_after_timeout"
                analysis.started_at = None
                await session.commit()

                await self.enqueue_analysis(
                    analysis_id=analysis.id,
                    project_id=analysis.project_id,
                    dataset_id=analysis.dataset_id,
                    question=analysis.question,
                    attempt=next_attempt,
                )

                recovered += 1

        return recovered

    async def _get_stale_analysis_ids(self) -> list[str]:
        from datetime import datetime, timedelta, timezone

        from sqlalchemy import select

        from app.db.session import AsyncSessionLocal
        from app.models.analysis import Analysis
        from app.schemas.analysis import AnalysisStatus

        cutoff = datetime.now(timezone.utc) - timedelta(
            seconds=self.settings.analysis_timeout_seconds,
        )

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Analysis.id).where(
                    Analysis.status == AnalysisStatus.RUNNING.value,
                    Analysis.started_at < cutoff,
                )
            )

            return [str(row) for row in result.scalars().all()]
