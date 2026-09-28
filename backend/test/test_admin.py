from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_user_controls(api_client) -> None:
    client, _, _, auth_headers = api_client

    signup_response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "member@example.com",
            "password": "strong-password",
            "name": "Member",
        },
    )

    assert signup_response.status_code == 201

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "member@example.com",
            "password": "strong-password",
        },
    )

    member_token = login_response.json()["access_token"]
    member_headers = {
        "Authorization": f"Bearer {member_token}",
    }

    denied_response = await client.get(
        "/api/v1/admin/users",
        headers=member_headers,
    )

    assert denied_response.status_code == 403

    users_response = await client.get(
        "/api/v1/admin/users",
        headers=auth_headers,
    )

    assert users_response.status_code == 200
    users = users_response.json()
    member = next(
        user for user in users
        if user["email"] == "member@example.com"
    )

    active_response = await client.post(
        f"/api/v1/admin/users/{member['id']}/active",
        headers=auth_headers,
        json={
            "is_active": False,
        },
    )

    assert active_response.status_code == 200
    assert active_response.json()["is_active"] is False
