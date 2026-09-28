from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_retry_cancel_and_export(api_client) -> None:
    client, queue, _ = api_client

    project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": "Controls Test",
            "description": "Retry, cancel, export",
        },
    )

    assert project_response.status_code == 201
    project = project_response.json()
    project_id = project["id"]

    upload_response = await client.post(
        f"/api/v1/projects/{project_id}/datasets",
        files={
            "file": (
                "sample.csv",
                b"a,b\n1,2\n3,4\n",
                "text/csv",
            )
        },
    )

    assert upload_response.status_code == 201
    dataset = upload_response.json()
    dataset_id = dataset["id"]

    analysis_response = await client.post(
        f"/api/v1/projects/{project_id}/analyses",
        json={
            "dataset_id": dataset_id,
            "question": "Analyze this dataset.",
        },
    )

    assert analysis_response.status_code == 201
    analysis = analysis_response.json()
    analysis_id = analysis["id"]

    retry_response = await client.post(
        f"/api/v1/projects/{project_id}/analyses/{analysis_id}/retry",
    )

    assert retry_response.status_code == 200
    retried = retry_response.json()

    assert retried["status"] == "queued"
    assert retried["attempt"] == 1
    assert len(queue.enqueued) == 2

    cancel_response = await client.post(
        f"/api/v1/projects/{project_id}/analyses/{analysis_id}/cancel",
    )

    assert cancel_response.status_code == 200
    cancelled = cancel_response.json()

    assert cancelled["status"] == "cancelled"

    history_response = await client.get(
        f"/api/v1/projects/{project_id}/analyses?status=cancelled",
    )

    assert history_response.status_code == 200
    assert history_response.json()[0]["status"] == "cancelled"

    export_response = await client.get(
        f"/api/v1/projects/{project_id}/analyses/{analysis_id}/export?format=json",
    )

    assert export_response.status_code == 200
    assert export_response.headers["content-type"].startswith(
        "application/json",
    )
