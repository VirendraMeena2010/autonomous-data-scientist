from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_signup_login_me(api_client) -> None:
    client, _, _ = api_client

    signup_response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test@example.com",
            "password": "strong-password",
            "name": "Test User",
        },
    )

    assert signup_response.status_code == 201

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "strong-password",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert me_response.status_code == 200
    assert me_response.json()["email"] == "test@example.com"
