from __future__ import annotations

import json

from redis.asyncio import Redis

from app.config import Settings


class AnalysisQueueError(RuntimeError):
    pass


class AnalysisQueue:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.redis = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )

    async def initialize(self) -> None:
        await self.ping()

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

        try:
            await self.redis.rpush(
                self.settings.background_queue_name,
                json.dumps(payload, separators=(",", ":")),
            )
        except Exception as exc:
            raise AnalysisQueueError("analysis_queue_unavailable") from exc
