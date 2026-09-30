from __future__ import annotations

import hashlib
import mimetypes
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile

from app.config import Settings
from app.services.file_scanner import FileScanner
from app.services.storage import (
    StorageService,
    dataset_destination,
    sanitize_filename,
)


class DatasetUploadError(RuntimeError):
    pass


class UnsupportedDatasetError(DatasetUploadError):
    pass


class UploadTooLargeError(DatasetUploadError):
    pass


class InvalidDatasetContentError(DatasetUploadError):
    pass


@dataclass(frozen=True)
class StagedDatasetUpload:
    project_id: str
    dataset_id: str
    original_filename: str
    destination: str
    media_type: str
    size_bytes: int
    sha256: str
    temporary_path: Path


async def stage_uploaded_dataset(
    upload: UploadFile,
    *,
    project_id: UUID | str,
    dataset_id: UUID | str,
    settings: Settings,
    scanner: FileScanner | None = None,
) -> StagedDatasetUpload:

    try:
        original_filename = sanitize_filename(
            upload.filename or ""
        )

    except Exception as exc:
        raise UnsupportedDatasetError(
            "invalid_filename"
        ) from exc

    suffix = (
        Path(original_filename)
        .suffix
        .lower()
    )

    if (
        suffix
        not in settings.dataset_extensions_list
    ):
        raise UnsupportedDatasetError(
            "unsupported_dataset_extension"
        )

    fd, temp_name = tempfile.mkstemp(
        prefix="ads-dataset-",
        suffix=suffix,
    )

    os.close(fd)

    temporary_path = Path(temp_name)

    digest = hashlib.sha256()
    size_bytes = 0

    try:
        with temporary_path.open("wb") as handle:

            while True:
                chunk = await upload.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                size_bytes += len(chunk)

                if (
                    size_bytes
                    > settings.max_upload_bytes
                ):
                    raise UploadTooLargeError(
                        "upload_too_large"
                    )

                digest.update(chunk)
                handle.write(chunk)

        await _validate_dataset_content(
            temporary_path,
            suffix,
        )

        if scanner is not None:
            await scanner.scan(
                temporary_path
            )

        detected_type, _ = (
            mimetypes.guess_type(
                original_filename
            )
        )

        media_type = (
            detected_type
            or upload.content_type
            or "application/octet-stream"
        )

        return StagedDatasetUpload(
            project_id=str(project_id),
            dataset_id=str(dataset_id),
            original_filename=original_filename,
            destination=dataset_destination(
                str(project_id),
                str(dataset_id),
                original_filename,
            ),
            media_type=media_type,
            size_bytes=size_bytes,
            sha256=digest.hexdigest(),
            temporary_path=temporary_path,
        )

    except BaseException:
        temporary_path.unlink(
            missing_ok=True
        )
        raise


async def _validate_dataset_content(
    path: Path,
    suffix: str,
) -> None:

    mime = await _detect_mime(path)

    allowed = {
        ".csv": {
            "text/csv",
            "application/csv",
            "text/plain",
            "application/octet-stream",
            "application/vnd.ms-excel",
        },
        ".parquet": {
            "application/vnd.apache.parquet",
            "application/octet-stream",
        },
        ".json": {
            "application/json",
            "text/plain",
            "application/octet-stream",
        },
        ".jsonl": {
            "application/json",
            "application/x-ndjson",
            "text/plain",
            "application/octet-stream",
        },
    }

    allowed_mimes = allowed.get(
        suffix,
        set(),
    )

    if mime not in allowed_mimes:
        raise InvalidDatasetContentError(
            "invalid_dataset_content_type"
        )


async def _detect_mime(
    path: Path,
) -> str:

    mime, _ = mimetypes.guess_type(
        path.name
    )

    return (
        mime
        or "application/octet-stream"
    )


async def persist_staged_dataset_upload(
    staged: StagedDatasetUpload,
    storage: StorageService,
) -> None:

    await storage.save_file(
        staged.temporary_path,
        staged.destination,
    )


def cleanup_staged_upload(
    staged: StagedDatasetUpload,
) -> None:

    staged.temporary_path.unlink(
        missing_ok=True
    )