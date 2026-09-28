from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from app.models.analysis import Dataset

from app.auth.passwords import hash_password
from app.models.user import User
from app.schemas.user import SignupInput


async def get_user_by_email(
    session: AsyncSession,
    email: str,
) -> User | None:
    result = await session.execute(
        select(User).where(User.email == email.lower())
    )

    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    payload: SignupInput,
) -> User:
    user = User(
        email=payload.email.lower(),
        name=payload.name,
        hashed_password=hash_password(payload.password),
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


async def get_storage_used_bytes(
    session: AsyncSession,
    user_id: str,
) -> int:
    result = await session.execute(
        select(func.sum(Dataset.size_bytes)).where(
            Dataset.owner_id == user_id,
        )
    )

    return int(result.scalar_one() or 0)
