from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.db.dependencies import get_db_session
from app.models.user import User
from app.services.queue_dashboard import QueueDashboardService

router = APIRouter(
    prefix="/queue",
    tags=["queue"],
)


@router.get("/stats")
async def queue_stats(
    _: User = Depends(require_admin),
):
    service = QueueDashboardService()

    try:
        return await service.stats()
    finally:
        await service.close()


@router.get("/dead-letter")
async def dead_letter_list(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _: User = Depends(require_admin),
):
    service = QueueDashboardService()

    try:
        return await service.dead_letter_list(
            limit=limit,
            offset=offset,
        )
    finally:
        await service.close()


@router.post("/dead-letter/{index}/replay")
async def replay_dead_letter(
    index: int,
    _: User = Depends(require_admin),
):
    service = QueueDashboardService()

    try:
        try:
            return await service.replay_dead_letter(index)
        except KeyError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="dead_letter_item_not_found",
            ) from exc
    finally:
        await service.close()
