from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.db.dependencies import get_db_session
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogRead

router = APIRouter(
    prefix="/audit-logs",
    tags=["audit-logs"],
    dependencies=[Depends(require_admin)],
)


@router.get(
    "",
    response_model=list[AuditLogRead],
)
async def list_audit_logs(
    session: AsyncSession = Depends(get_db_session),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    event: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    actor_id: str | None = Query(default=None),
):
    query = (
        select(AuditLog)
        .order_by(AuditLog.created_at.desc(), AuditLog.id)
        .offset(offset)
        .limit(limit)
    )

    if event:
        query = query.where(AuditLog.event == event)

    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)

    if actor_id:
        query = query.where(AuditLog.actor_id == actor_id)

    result = await session.execute(query)

    return list(result.scalars().all())
