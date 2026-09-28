from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import Analysis, Dataset


async def get_project_summary(
    session: AsyncSession,
    project_id: UUID | str,
    owner_id: str,
) -> dict[str, object]:
    dataset_count = await _scalar_int(
        session,
        select(func.count(Dataset.id)).where(
            Dataset.project_id == str(project_id),
            Dataset.owner_id == owner_id,
        ),
    )

    analysis_count = await _scalar_int(
        session,
        select(func.count(Analysis.id)).where(
            Analysis.project_id == str(project_id),
            Analysis.owner_id == owner_id,
        ),
    )

    succeeded_count = await _scalar_int(
        session,
        select(func.count(Analysis.id)).where(
            Analysis.project_id == str(project_id),
            Analysis.owner_id == owner_id,
            Analysis.status == "succeeded",
        ),
    )

    failed_count = await _scalar_int(
        session,
        select(func.count(Analysis.id)).where(
            Analysis.project_id == str(project_id),
            Analysis.owner_id == owner_id,
            Analysis.status == "failed",
        ),
    )

    return {
        "project_id": str(project_id),
        "dataset_count": dataset_count,
        "analysis_count": analysis_count,
        "succeeded_count": succeeded_count,
        "failed_count": failed_count,
        "success_rate": (
            succeeded_count / analysis_count
            if analysis_count
            else 0.0
        ),
    }


async def _scalar_int(
    session: AsyncSession,
    statement,
) -> int:
    result = await session.execute(statement)
    return int(result.scalar_one() or 0)
