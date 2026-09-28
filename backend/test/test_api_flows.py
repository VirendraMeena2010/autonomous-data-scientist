from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.services.storage import StorageService


@pytest.mark.asyncio
async def test_project_dataset_analysis_flow(
    api_client: tuple[AsyncClient, object, StorageService],
) -> None:
    client, queue, storage = api_client

    create_project_response = await client.post(
        "/api/v1/projects",
        json={
            "name": "Customer Analytics",
            "description": "Test project",
        },
    )

    assert create_project_response.status_code == 201
    project = create_project_response.json()
    project_id = project["id"]

    list_projects_response = await client.get("/api/v1/projects")
    assert list_projects_response.status_code == 200
    assert len(list_projects_response.json()) == 1

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

    assert upload_response.status_code == 201, upload_response.text

    dataset = upload_response.json()
    dataset_id = dataset["id"]

    assert dataset["row_count"] == 2
    assert dataset["column_count"] == 2
    assert dataset["status"] == "uploaded"

    create_analysis_response = await client.post(
        f"/api/v1/projects/{project_id}/analyses",
        json={
            "dataset_id": dataset_id,
            "question": "What is the relationship between a and b?",
        },
    )

    assert create_analysis_response.status_code == 201
    analysis = create_analysis_response.json()

    assert analysis["status"] == "queued"
    assert queue.enqueued
    assert queue.enqueued[0]["analysis_id"] == analysis["id"]
    assert queue.enqueued[0]["dataset_id"] == dataset_id

    delete_response = await client.delete(
        f"/api/v1/projects/{project_id}",
    )

    assert delete_response.status_code == 204
    assert not await storage.exists(dataset["stored_path"])
