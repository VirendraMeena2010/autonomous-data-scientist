from __future__ import annotations

from redis.asyncio import Redis


def cancellation_key(analysis_id: str) -> str:
    return f"ads:analysis:{analysis_id}:cancel"


async def request_cancellation(
    redis: Redis,
    analysis_id: str,
    *,
    ttl_seconds: int = 3600,
) -> None:
    await redis.set(
        cancellation_key(analysis_id),
        "1",
        ex=max(1, ttl_seconds),
    )


async def cancellation_requested(
    redis: Redis,
    analysis_id: str,
) -> bool:
    value = await redis.get(cancellation_key(analysis_id))
    return value is not None


async def clear_cancellation(
    redis: Redis,
    analysis_id: str,
) -> None:
    await redis.delete(cancellation_key(analysis_id))
