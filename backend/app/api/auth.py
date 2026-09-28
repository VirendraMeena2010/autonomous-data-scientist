"""from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi.util import get_remote_address

from app.rate_limit import limiter
from app.services.users import get_storage_used_bytes, create_user, get_user_by_email
from app.config import settings
from app.auth.dependencies import get_current_user
from app.auth.jwt import create_access_token
from app.auth.passwords import verify_password
from app.auth.schemas import LoginInput, SignupInput, UserRead
from app.db.dependencies import get_db_session
from app.models.user import User

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@router.post(
    "/signup",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(f"{settings.rate_limit_auth_per_minute} per minute")
async def signup(
    request: Request,
    payload: SignupInput,
    session: AsyncSession = Depends(get_db_session),
) -> User:
    existing = await get_user_by_email(
        session,
        payload.email,
    )

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="email_already_registered",
        )

    return await create_user(
        session,
        payload,
    )

@router.post(
    "/login",
)
@limiter.limit(f"{settings.rate_limit_auth_per_minute} per minute")
async def login(
    request: Request,
    payload: LoginInput,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    user = await get_user_by_email(
        session,
        payload.email,
    )

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_email_or_password",
        )

    if not verify_password(
        payload.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_email_or_password",
        )

    return {
        "access_token": create_access_token(
            user_id=user.id,
        ),
        "token_type": "bearer",
    }

@router.get("/me")
async def me(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    user.storage_used_bytes = await get_storage_used_bytes(
        session,
        user.id,
    )

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "storage_quota_bytes": user.storage_quota_bytes,
        "storage_used_bytes": user.storage_used_bytes,
    }"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.users import (
    get_storage_used_bytes,
    create_user,
    get_user_by_email,
)
from app.auth.dependencies import get_current_user
from app.auth.jwt import create_access_token
from app.auth.passwords import verify_password
from app.auth.schemas import LoginInput, SignupInput, UserRead
from app.db.dependencies import get_db_session
from app.models.user import User


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/signup",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def signup(
    payload: SignupInput,
    session: AsyncSession = Depends(get_db_session),
) -> User:
    existing = await get_user_by_email(
        session,
        payload.email,
    )
    
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="email_already_registered",
        )

    return await create_user(
        session,
        payload,
    )


@router.post(
    "/login",
)
async def login(
    payload: LoginInput,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    user = await get_user_by_email(
        session,
        payload.email,
    )
    
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_email_or_password",
        )

    if not verify_password(
        payload.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_email_or_password",
        )

    return {
        "access_token": create_access_token(
            user_id=user.id,
        ),
        "token_type": "bearer",
    }


@router.get("/me")
async def me(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    user.storage_used_bytes = await get_storage_used_bytes(
        session,
        user.id,
    )
    
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "storage_quota_bytes": user.storage_quota_bytes,
        "storage_used_bytes": user.storage_used_bytes,
    }