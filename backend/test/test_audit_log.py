from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_can_list_audit_logs(api_client) -> None:
    client, _, _, auth_headers = api_client

    response = await client.get(
        "/api/v1/audit-logs",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == []
