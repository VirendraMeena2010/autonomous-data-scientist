from __future__ import annotations

import json
from typing import Any

from redis.asyncio import Redis

from app.config import settings


class QueueDashboardService:
    def __init__(self) -> None:
        self.redis = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )

    async def close(self) -> None:
        await self.redis.aclose()

    async def stats(self) -> dict[str, int | str]:
        queue = settings.background_queue_name
        dead_letter = f"{queue}:dead_letter"

        return {
            "queue": queue,
            "pending": await self.redis.llen(queue),
            "dead_letter": await self.redis.llen(dead_letter),
        }

    async def dead_letter_list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        dead_letter = f"{settings.background_queue_name}:dead_letter"

        items = await self.redis.lrange(
            dead_letter,
            offset,
            offset + limit - 1,
        )

        parsed = []

        for item in items:
            try:
                parsed.append(json.loads(item))
            except json.JSONDecodeError:
                parsed.append(
                    {
                        "raw": item,
                        "parse_error": True,
                    }
                )

        return parsed

    async def replay_dead_letter(self, index: int) -> dict[str, Any]:
        dead_letter = f"{settings.background_queue_name}:dead_letter"

        raw = await self.redis.lindex(dead_letter, index)

        if raw is None:
            raise KeyError("dead_letter_item_not_found")

        payload = json.loads(raw)

        if payload.get("event") == "analysis.dead_letter":
            payload["event"] = "analysis.requested"
            payload.pop("error", None)

        await self.redis.rpush(
            settings.background_queue_name,
            json.dumps(payload, separators=(",", ":")),
        )

        await self.redis.lrem(dead_letter, 1, raw)

        return payload
