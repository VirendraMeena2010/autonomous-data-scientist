from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import Project
from app.schemas.analysis import ProjectCreate


async def create_project(
    session: AsyncSession,
    payload: ProjectCreate,
    owner_id: str,
) -> Project:
    project = Project(
        name=payload.name,
        description=payload.description,
        owner_id=owner_id,
    )

    session.add(project)
    await session.commit()
    await session.refresh(project)

    return project


async def list_projects(
    session: AsyncSession,
    owner_id: str,
    *,
    limit: int,
    offset: int,
) -> list[Project]:
    result = await session.execute(
        select(Project)
        .where(Project.owner_id == owner_id)
        .order_by(Project.created_at.desc(), Project.id)
        .offset(offset)
        .limit(limit)
    )

    return list(result.scalars().all())


async def get_project(
    session: AsyncSession,
    project_id: UUID | str,
) -> Project | None:
    result = await session.execute(
        select(Project).where(Project.id == str(project_id))
    )

    return result.scalar_one_or_none()
