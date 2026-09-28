from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from app import models  # noqa: F401
from app.auth.jwt import create_access_token
from app.auth.passwords import hash_password
from app.config import Settings
from app.db.base import Base
from app.db.dependencies import get_db_session, get_current_user
from app.main import app
from app.models.user import User
from app.services.storage import StorageService

# Move engine and sessionmaker to module scope so helper functions can use them
engine = create_async_engine("sqlite+aiosqlite:///:memory:")
TestingSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def set(
        self,
        key: str,
        value: str,
        ex: int | None = None,
    ) -> None:
        self.values[key] = value

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def delete(self, key: str) -> None:
        self.values.pop(key, None)


class FakeQueue:
    def __init__(self) -> None:
        self.redis = FakeRedis()
        self.enqueued: list[dict[str, object]] = []

    async def enqueue_analysis(self, **payload: object) -> None:
        self.enqueued.append(payload)


@pytest.fixture
async def api_client(
    tmp_path: Path,
) -> AsyncIterator[tuple[AsyncClient, FakeQueue, StorageService, dict[str, str]]]:
    # Initialize schema once at the start of the fixture lifetime
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db

    fake_queue = FakeQueue()
    storage = StorageService() 

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        user = User(
            id="test-user-id",
            email="test@example.com",
            name="Test User",
            hashed_password=hash_password("password"),
        )

        async with TestingSessionLocal() as session:
            session.add(user)
            await session.commit()

        token = create_access_token(user_id=user.id)
        auth_headers = {
            "Authorization": f"Bearer {token}",
        }

        async def override_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user

        yield test_client, fake_queue, storage, auth_headers

    app.dependency_overrides.clear()
    
    # Drop all tables to clean up schema state between tests
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


async def seed_dataset(project_id: str) -> str:
    from app.models.analysis import Dataset

    async with TestingSessionLocal() as session:
        dataset = Dataset(
            project_id=project_id,
            original_filename="sample.csv",
            stored_path="projects/sample.csv",
            media_type="text/csv",
            size_bytes=123,
            sha256="abc",
            row_count=10,
            column_count=2,
            status="uploaded",
            owner_id="test-user-id",
        )
        session.add(dataset)
        await session.commit()
        await session.refresh(dataset)
        return dataset.id
