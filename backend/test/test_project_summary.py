from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_project_summary(api_client) -> None:
    client, _, _, auth_headers = api_client

    project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": "Summary Test",
            "description": "Summary",
        },
        headers=auth_headers,
    )

    assert project_response.status_code == 201
    project = project_response.json()
    project_id = project["id"]

    summary_response = await client.get(
        f"/api/v1/projects/{project_id}/summary",
        headers=auth_headers,
    )

    assert summary_response.status_code == 200

    summary = summary_response.json()

    assert summary["project_id"] == project_id
    assert summary["dataset_count"] == 0
    assert summary["analysis_count"] == 0
    assert summary["success_rate"] == 0.0
