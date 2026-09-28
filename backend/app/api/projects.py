from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_storage
from app.auth.dependencies import get_current_user
from app.db.dependencies import get_db_session
from app.models.analysis import Dataset, Project
from app.models.user import User
from app.schemas.analysis import (
    ProjectCreate,
    ProjectRead,
    ProjectSummary,
)
from app.services.project_summaries import get_project_summary
from app.services.ownership import require_project_owner
from app.services.storage import StorageError

logger = structlog.get_logger()

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
)


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_project_endpoint(
    payload: ProjectCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Project:
    project = Project(
        name=payload.name,
        description=payload.description,
        owner_id=user.id,
    )

    session.add(project)
    await session.commit()
    await session.refresh(project)

    return project


@router.get(
    "",
    response_model=list[ProjectRead],
)
async def list_projects_endpoint(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[Project]:
    result = await session.execute(
        select(Project)
        .where(Project.owner_id == user.id)
        .order_by(Project.created_at.desc(), Project.id)
        .offset(offset)
        .limit(limit)
    )

    return list(result.scalars().all())


@router.get(
    "/{project_id}",
    response_model=ProjectRead,
)
async def get_project_endpoint(
    project_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Project:
    return await require_project_owner(
        session,
        project_id,
        user.id,
    )


@router.get(
    "/{project_id}/summary",
    response_model=ProjectSummary,
)
async def project_summary_endpoint(
    project_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    project = await require_project_owner(
        session,
        project_id,
        user.id,
    )

    return await get_project_summary(
        session,
        project.id,
        user.id,
    )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project_endpoint(
    project_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    storage=Depends(get_storage),
) -> None:
    project = await require_project_owner(
        session,
        project_id,
        user.id,
    )

    result = await session.execute(
        select(Dataset).where(Dataset.project_id == project.id)
    )

    for dataset in result.scalars().all():
        try:
            await storage.delete_file(dataset.stored_path)
        except StorageError as exc:
            logger.warning(
                "dataset_storage_delete_failed",
                dataset_id=dataset.id,
                error=str(exc),
            )

    await session.delete(project)
    await session.commit()

    return None
