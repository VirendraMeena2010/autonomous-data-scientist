from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Literal
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.dependencies import get_db_session
from app.models.analysis import Analysis as AnalysisModel
from app.models.analysis import utc_now
from app.models.user import User
from app.schemas.analysis import (
    AnalysisCreate,
    AnalysisRead,
    AnalysisStatus as AnalysisStatusEnum,
)
from app.services.analysis_export import render_analysis_export
from app.services.datasets import get_dataset_for_project
from app.services.ownership import (
    require_analysis_owner,
    require_project_owner,
)
from app.services.storage import StorageService


router = APIRouter(
    prefix="/projects",
    tags=["analyses"],
)


async def run_analysis_directly(
    analysis: AnalysisModel,
    dataset,
    session: AsyncSession,
    request: Request,
    storage: StorageService,
) -> None:
    """
    Run the LangGraph analysis workflow.

    The database stores the dataset's object-storage key in
    `stored_path`. The analysis graph requires a real local
    filesystem path, so the dataset is downloaded to a temporary
    file before invoking the graph.

    Only JSON-safe values are passed into LangGraph state.
    SQLAlchemy ORM objects are never placed in graph state.
    """

    analysis.status = AnalysisStatusEnum.RUNNING.value
    analysis.started_at = utc_now()

    await session.commit()
    await session.refresh(analysis)

    temporary_path: Path | None = None

    try:
        # ---------------------------------------------------------
        # 1. Get LangGraph
        # ---------------------------------------------------------
        graph = request.app.state.analysis_graph

        # ---------------------------------------------------------
        # 2. Resolve dataset from storage
        # ---------------------------------------------------------
        # IMPORTANT:
        # Do NOT call storage.local_path() directly here.
        # storage.local_path() only works when STORAGE_BACKEND=local
        # When STORAGE_BACKEND=s3, the dataset must first be
        # downloaded from object storage into a temporary local path.
        # ---------------------------------------------------------
        temp_dir = Path(tempfile.gettempdir()) / "autonomous-data-scientist" / str(analysis.id)
        temp_dir.mkdir(parents=True, exist_ok=True)

        if storage.backend == "local":
            temporary_path = storage.local_path(dataset.stored_path)
        else:
            temporary_path = temp_dir / Path(dataset.original_filename).name
            await storage.download_file(dataset.stored_path, temporary_path)

        # ---------------------------------------------------------
        # 3. Build JSON-safe metadata
        # ---------------------------------------------------------
        raw_metadata = getattr(dataset, "dataset_metadata", None)
        dataset_metadata = dict(raw_metadata) if isinstance(raw_metadata, dict) else {}

        dataset_metadata.update(
            {
                "filename": str(dataset.original_filename),
                "original_filename": str(dataset.original_filename),
                "media_type": str(dataset.media_type) if dataset.media_type is not None else None,
                "size_bytes": int(dataset.size_bytes) if dataset.size_bytes is not None else None,
                "row_count": int(dataset.row_count) if dataset.row_count is not None else None,
                "column_count": int(dataset.column_count) if dataset.column_count is not None else None,
                "status": str(dataset.status) if dataset.status is not None else None,
            }
        )

        # ---------------------------------------------------------
        # 4. Build LangGraph state
        # ---------------------------------------------------------
        initial_state = {
            "analysis_id": str(analysis.id),
            "project_id": str(analysis.project_id),
            "dataset_id": str(analysis.dataset_id),
            "question": str(analysis.question),
            # This is now a real local filesystem path.
            "dataset_path": str(temporary_path),
            # Only JSON-safe values.
            "dataset_metadata": dataset_metadata,
            "plan": None,
            "profile": None,
            "quality": None,
            "analysis_results": [],
            "findings": None,
            "report": None,
            "guardrail": None,
            "report_guardrail": None,
            "langfuse_trace_id": None,
            "errors": [],
        }

        # ---------------------------------------------------------
        # 5. LangGraph configuration
        # ---------------------------------------------------------
        config = {
            "configurable": {
                "thread_id": str(analysis.id),
            }
        }

        # ---------------------------------------------------------
        # 6. Execute graph
        # ---------------------------------------------------------
        result = await graph.ainvoke(initial_state, config=config)

        # ---------------------------------------------------------
        # 7. Persist graph results
        # ---------------------------------------------------------
        analysis.plan = result.get("plan")
        analysis.profile = result.get("profile")
        analysis.quality = result.get("quality")
        analysis.findings = result.get("findings")
        analysis.report = result.get("report")
        analysis.guardrail = result.get("guardrail")

        report_guardrail = result.get("report_guardrail")
        if report_guardrail is not None:
            analysis.guardrail = report_guardrail

        analysis.langfuse_trace_id = result.get("langfuse_trace_id")

        # IMPORTANT: Enum defines SUCCEEDED, not COMPLETED.
        analysis.status = AnalysisStatusEnum.SUCCEEDED.value
        analysis.finished_at = utc_now()
        analysis.error_message = None

        await session.commit()
        await session.refresh(analysis)

    except Exception as exc:
        # ---------------------------------------------------------
        # 8. Persist failure
        # ---------------------------------------------------------
        analysis.status = AnalysisStatusEnum.FAILED.value
        analysis.error_message = str(exc)
        analysis.finished_at = utc_now()

        await session.commit()
        await session.refresh(analysis)
        raise

    finally:
        # ---------------------------------------------------------
        # 9. Remove temporary dataset
        # ---------------------------------------------------------
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
                parent = temporary_path.parent
                if parent.exists() and not any(parent.iterdir()):
                    parent.rmdir()
            except OSError:
                pass


@router.post(
    "/{project_id}/analyses",
    response_model=AnalysisRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_analysis_endpoint(
    project_id: UUID,
    payload: AnalysisCreate,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    # ---------------------------------------------------------
    # 1. Verify project ownership
    # ---------------------------------------------------------
    project = await require_project_owner(session, project_id, user.id)

    # ---------------------------------------------------------
    # 2. Get dataset belonging to project
    # ---------------------------------------------------------
    dataset = await get_dataset_for_project(session, project_id, payload.dataset_id)

    if dataset is None or dataset.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="dataset_not_found",
        )

    # ---------------------------------------------------------
    # 3. Get storage service
    # ---------------------------------------------------------
    storage = getattr(request.app.state, "storage", None)

    if storage is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="storage_not_initialized",
        )

    # ---------------------------------------------------------
    # 4. Create analysis record
    # ---------------------------------------------------------
    analysis = AnalysisModel(
        project_id=project.id,
        dataset_id=str(payload.dataset_id),
        owner_id=user.id,
        question=payload.question,
        status=AnalysisStatusEnum.QUEUED.value,
        attempt=0,
    )

    session.add(analysis)
    await session.commit()
    await session.refresh(analysis)

    # ---------------------------------------------------------
    # 5. Execute analysis
    # ---------------------------------------------------------
    try:
        await run_analysis_directly(
            analysis=analysis,
            dataset=dataset,
            session=session,
            request=request,
            storage=storage,
        )
    except Exception:
        # The analysis record already contains the actual failure.
        pass

    return analysis


@router.get(
    "/{project_id}/analyses",
    response_model=list[AnalysisRead],
)
async def list_analyses_endpoint(
    project_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: AnalysisStatusEnum | None = Query(default=None),
):
    await require_project_owner(session, project_id, user.id)

    query = (
        select(AnalysisModel)
        .where(
            AnalysisModel.project_id == str(project_id),
            AnalysisModel.owner_id == user.id,
        )
        .order_by(
            AnalysisModel.created_at.desc(),
            AnalysisModel.id,
        )
        .offset(offset)
        .limit(limit)
    )

    if status_filter is not None:
        query = query.where(AnalysisModel.status == status_filter.value)

    result = await session.execute(query)
    return list(result.scalars().all())


@router.post(
    "/{project_id}/analyses/{analysis_id}/cancel",
    response_model=AnalysisRead,
)
async def cancel_analysis_endpoint(
    project_id: UUID,
    analysis_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    analysis = await require_analysis_owner(session, project_id, analysis_id, user.id)

    if analysis.status not in {
        AnalysisStatusEnum.QUEUED.value,
        AnalysisStatusEnum.RUNNING.value,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="analysis_not_cancelable",
        )

    analysis.status = AnalysisStatusEnum.CANCELLED.value
    analysis.error_message = "cancelled_by_user"
    analysis.finished_at = utc_now()

    await session.commit()
    await session.refresh(analysis)

    return analysis


@router.get(
    "/{project_id}/analyses/{analysis_id}/export",
)
async def export_analysis_endpoint(
    project_id: UUID,
    analysis_id: UUID,
    export_format: Literal["json", "markdown"] = Query("json"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    analysis = await require_analysis_owner(session, project_id, analysis_id, user.id)
    content, media_type, filename = render_analysis_export(analysis, export_format)

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get(
    "/{project_id}/analyses/{analysis_id}",
    response_model=AnalysisRead,
)
async def get_analysis_endpoint(
    project_id: UUID,
    analysis_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await require_analysis_owner(session, project_id, analysis_id, user.id)