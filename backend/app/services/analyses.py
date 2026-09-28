from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import Analysis


async def get_analysis_for_project(
    session: AsyncSession,
    project_id: UUID | str,
    analysis_id: UUID | str,
) -> Analysis | None:
    result = await session.execute(
        select(Analysis).where(
            Analysis.project_id == str(project_id),
            Analysis.id == str(analysis_id),
        )
    )

    return result.scalar_one_or_none()
