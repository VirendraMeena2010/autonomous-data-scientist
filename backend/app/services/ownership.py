from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import Analysis, Dataset, Project


async def require_project_owner(
    session: AsyncSession,
    project_id: UUID | str,
    user_id: str,
) -> Project:
    result = await session.execute(
        select(Project).where(
            Project.id == str(project_id),
            Project.owner_id == user_id,
        )
    )

    project = result.scalar_one_or_none()

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="project_not_found",
        )

    return project


async def require_dataset_owner(
    session: AsyncSession,
    project_id: UUID | str,
    dataset_id: UUID | str,
    user_id: str,
) -> Dataset:
    result = await session.execute(
        select(Dataset).where(
            Dataset.project_id == str(project_id),
            Dataset.id == str(dataset_id),
            Dataset.owner_id == user_id,
        )
    )

    dataset = result.scalar_one_or_none()

    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="dataset_not_found",
        )

    return dataset


async def require_analysis_owner(
    session: AsyncSession,
    project_id: UUID | str,
    analysis_id: UUID | str,
    user_id: str,
) -> Analysis:
    result = await session.execute(
        select(Analysis).where(
            Analysis.project_id == str(project_id),
            Analysis.id == str(analysis_id),
            Analysis.owner_id == user_id,
        )
    )

    analysis = result.scalar_one_or_none()

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="analysis_not_found",
        )

    return analysis
