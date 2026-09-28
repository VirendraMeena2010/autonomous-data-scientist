from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_storage
from app.auth.dependencies import get_current_user
from app.config import settings
from app.db.dependencies import get_db_session
from app.models.analysis import Dataset
from app.models.user import User
from app.rate_limit import limiter
from app.schemas.analysis import DatasetRead
from app.services.dataset_metadata import (
    DatasetMetadataError,
    extract_dataset_metadata,
)
from app.services.dataset_uploads import (
    DatasetUploadError,
    StagedDatasetUpload,
    cleanup_staged_upload,
    persist_staged_dataset_upload,
    stage_uploaded_dataset,
)
from app.services.file_scanner import FileScanner
from app.services.ids import new_id
from app.services.ownership import (
    require_dataset_owner,
    require_project_owner,
)
from app.services.storage import (
    StorageError,
    StorageService,
)

logger = structlog.get_logger()

router = APIRouter(
    prefix="/projects",
    tags=["datasets"],
)


async def get_user_storage_used_bytes(
    session: AsyncSession,
    user_id: str,
) -> int:
    result = await session.execute(
        select(
            func.sum(Dataset.size_bytes)
        ).where(
            Dataset.owner_id == user_id,
        )
    )

    return int(result.scalar_one() or 0)


@router.post(
    "/{project_id}/datasets",
    response_model=DatasetRead,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(
    f"{settings.rate_limit_auth_per_minute} per minute"
)
async def upload_dataset_endpoint(
    request: Request,
    project_id: UUID,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    storage: StorageService = Depends(get_storage),
) -> Dataset:

    project = await require_project_owner(
        session,
        project_id,
        user.id,
    )

    dataset_id = new_id()

    staged: StagedDatasetUpload | None = None
    persisted = False

    try:
        # ---------------------------------------------------------
        # 1. Stage uploaded file
        # ---------------------------------------------------------
        staged = await stage_uploaded_dataset(
            file,
            project_id=project.id,
            dataset_id=dataset_id,
            settings=settings,
            scanner=FileScanner(settings),
        )

        # ---------------------------------------------------------
        # 2. Check user storage quota
        # ---------------------------------------------------------
        used_bytes = await get_user_storage_used_bytes(
            session,
            user.id,
        )

        if (
            used_bytes + staged.size_bytes
            > user.storage_quota_bytes
        ):
            cleanup_staged_upload(staged)
            staged = None

            raise HTTPException(
                status_code=(
                    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
                ),
                detail="storage_quota_exceeded",
            )

        # ---------------------------------------------------------
        # 3. Extract dataset metadata
        # ---------------------------------------------------------
        metadata = await extract_dataset_metadata(
            staged.temporary_path,
            staged.original_filename,
        )

        # ---------------------------------------------------------
        # 4. Persist file to object storage
        # ---------------------------------------------------------
        await persist_staged_dataset_upload(
            staged,
            storage,
        )

        persisted = True

        # ---------------------------------------------------------
        # 5. Create database record
        # ---------------------------------------------------------
        dataset = Dataset(
            id=dataset_id,
            project_id=project.id,
            owner_id=user.id,
            original_filename=staged.original_filename,
            stored_path=staged.destination,
            media_type=staged.media_type,
            size_bytes=staged.size_bytes,
            sha256=staged.sha256,
            row_count=metadata["row_count"],
            column_count=metadata["column_count"],
            status="uploaded",

            # IMPORTANT:
            # Python attribute is dataset_metadata.
            # Database column remains "metadata".
            dataset_metadata=metadata,
        )

        session.add(dataset)

        await session.commit()
        await session.refresh(dataset)

        return dataset

    except DatasetUploadError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except DatasetMetadataError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail="dataset_metadata_extraction_failed",
        ) from exc

    except HTTPException:
        raise

    except Exception:
        # If object storage succeeded but DB creation failed,
        # remove the uploaded object so we don't leave an orphan.
        if staged is not None and persisted:
            try:
                await storage.delete_file(
                    staged.destination
                )
            except StorageError:
                logger.warning(
                    "dataset_storage_cleanup_failed",
                    destination=staged.destination,
                )

        # Roll back the SQLAlchemy transaction.
        await session.rollback()

        raise

    finally:
        if staged is not None:
            cleanup_staged_upload(staged)


@router.get(
    "/{project_id}/datasets",
    response_model=list[DatasetRead],
)
async def list_datasets_endpoint(
    project_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[Dataset]:

    await require_project_owner(
        session,
        project_id,
        user.id,
    )

    result = await session.execute(
        select(Dataset)
        .where(
            Dataset.project_id == str(project_id),
            Dataset.owner_id == user.id,
        )
        .order_by(
            Dataset.created_at.desc(),
            Dataset.id,
        )
    )

    return list(
        result.scalars().all()
    )


@router.get(
    "/{project_id}/datasets/{dataset_id}",
    response_model=DatasetRead,
)
async def get_dataset_endpoint(
    project_id: UUID,
    dataset_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dataset:

    return await require_dataset_owner(
        session,
        project_id,
        dataset_id,
        user.id,
    )


@router.delete(
    "/{project_id}/datasets/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_dataset_endpoint(
    project_id: UUID,
    dataset_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    storage: StorageService = Depends(get_storage),
) -> None:

    dataset = await require_dataset_owner(
        session,
        project_id,
        dataset_id,
        user.id,
    )

    try:
        await storage.delete_file(
            dataset.stored_path
        )

    except StorageError as exc:
        logger.warning(
            "dataset_storage_delete_failed",
            dataset_id=dataset.id,
            error=str(exc),
        )

    await session.delete(dataset)
    await session.commit()

    return None


@router.get(
    "/{project_id}/datasets/{dataset_id}/download-url",
)
async def dataset_download_url_endpoint(
    project_id: UUID,
    dataset_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    storage: StorageService = Depends(get_storage),
):
    dataset = await require_dataset_owner(
        session,
        project_id,
        dataset_id,
        user.id,
    )

    url = await storage.create_signed_download_url(
        dataset.stored_path,
        expires_in=300,
    )

    return {
        "url": url,
        "expires_in": 300,
    }