from __future__ import annotations

import structlog

from app.auth.passwords import hash_password
from app.config import settings
from app.db.session import AsyncSessionLocal
from app.models.user import User

logger = structlog.get_logger()


async def bootstrap_admin() -> None:
    email = (
        settings.bootstrap_admin_email
        or settings.bootstrap_admin_email
    )

    password = settings.bootstrap_admin_password

    if not email or not password:
        return

    async with AsyncSessionLocal() as session:
        existing = await session.execute(
            User.__table__.select().where(
                User.__table__.c.email == email.lower()
            )
        )

        if existing.first() is not None:
            logger.info(
                "bootstrap_admin_already_exists",
                email=email,
            )
            return

        user = User(
            email=email.lower(),
            name=settings.bootstrap_admin_name,
            hashed_password=hash_password(password),
            is_active=True,
            is_superuser=True,
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)

        logger.warning(
            "bootstrap_admin_created",
            user_id=user.id,
            email=user.email,
        )
