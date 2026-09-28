from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.db.dependencies import get_db_session
from app.models.user import User
from app.schemas.admin import (
    AdminUserRead,
    SetActiveInput,
    SetSuperuserInput,
)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


@router.get(
    "/users",
    response_model=list[AdminUserRead],
    dependencies=[Depends(require_admin)],
)
async def list_users(
    session: AsyncSession = Depends(get_db_session),
) -> list[User]:
    result = await session.execute(
        select(User)
        .order_by(User.created_at.desc(), User.id)
    )

    return list(result.scalars().all())


@router.post(
    "/users/{user_id}/active",
    response_model=AdminUserRead,
    dependencies=[Depends(require_admin)],
)
async def set_user_active(
    user_id: str,
    payload: SetActiveInput,
    session: AsyncSession = Depends(get_db_session),
) -> User:
    user = await _get_user_or_404(
        session,
        user_id,
    )

    user.is_active = payload.is_active
    await session.commit()
    await session.refresh(user)

    return user


@router.post(
    "/users/{user_id}/superuser",
    response_model=AdminUserRead,
    dependencies=[Depends(require_admin)],
)
async def set_user_superuser(
    user_id: str,
    payload: SetSuperuserInput,
    session: AsyncSession = Depends(get_db_session),
) -> User:
    user = await _get_user_or_404(
        session,
        user_id,
    )

    user.is_superuser = payload.is_superuser
    await session.commit()
    await session.refresh(user)

    return user


async def _get_user_or_404(
    session: AsyncSession,
    user_id: str,
) -> User:
    result = await session.execute(
        select(User).where(User.id == user_id)
    )

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user_not_found",
        )

    return user
