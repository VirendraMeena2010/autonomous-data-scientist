from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import structlog

logger = structlog.get_logger()


def audit_log(
    *,
    event: str,
    actor_id: str | None,
    actor_email: str | None,
    resource_type: str,
    resource_id: str | None,
    action: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    logger.info(
        "audit_event",
        event=event,
        actor_id=actor_id,
        actor_email=actor_email,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        metadata=metadata or {},
        occurred_at=datetime.now(timezone.utc).isoformat(),
    )

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def write_audit_log(
    session: AsyncSession,
    *,
    event: str,
    action: str,
    resource_type: str,
    actor_id: str | None = None,
    actor_email: str | None = None,
    resource_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    audit_log = AuditLog(
        actor_id=actor_id,
        actor_email=actor_email,
        event=event,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata_=metadata,
        created_at=datetime.now(timezone.utc),
    )

    session.add(audit_log)
    await session.commit()
    await session.refresh(audit_log)

    return audit_log

