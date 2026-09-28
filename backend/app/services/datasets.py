from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import Dataset


async def get_dataset_for_project(
    session: AsyncSession,
    project_id: UUID | str,
    dataset_id: UUID | str,
) -> Dataset | None:
    result = await session.execute(
        select(Dataset).where(
            Dataset.project_id == str(project_id),
            Dataset.id == str(dataset_id),
        )
    )

    return result.scalar_one_or_none()
