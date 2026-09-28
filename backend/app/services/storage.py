from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.config import Settings


class StorageError(RuntimeError):
    pass


def sanitize_filename(filename: str) -> str:
    name = Path(filename).name.strip()

    if not name or name in {".", ".."}:
        raise StorageError("invalid_filename")

    name = "".join(
        ch
        for ch in name
        if ch not in "\x00\r\n" and ord(ch) >= 32
    )

    suffix = Path(name).suffix
    stem = Path(name).stem

    if len(name) > 255:
        name = (
            f"{stem[:max(1, 255 - len(suffix))]}"
            f"{suffix}"
        )

    return name


def dataset_destination(
    project_id: str,
    dataset_id: str,
    filename: str,
) -> str:
    safe_name = sanitize_filename(filename)

    return (
        f"projects/{project_id}/datasets/"
        f"{dataset_id}/{safe_name}"
    )


class StorageService:

    def __init__(
        self,
        settings: Settings,
    ) -> None:

        self.settings = settings
        self.backend = settings.storage_backend

        self.root = (
            settings.local_storage_path
            .expanduser()
            .resolve()
        )

        self._s3_client: Any | None = None

        if self.backend == "s3":
            session = boto3.session.Session()

            self._s3_client = session.client(
                "s3",
                endpoint_url=settings.s3_endpoint_url,
                region_name=settings.s3_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
            )

    async def initialize(self) -> None:
        if self.backend == "local":
            self.root.mkdir(
                parents=True,
                exist_ok=True,
            )
            return

        await asyncio.to_thread(
            self._ensure_bucket
        )

    async def ping(self) -> bool:
        if self.backend == "local":
            return await asyncio.to_thread(
                self.root.is_dir
            )

        await asyncio.to_thread(
            self._ensure_bucket
        )

        return True

    def close(self) -> None:
        if self._s3_client is not None:
            self._s3_client.close()

    async def save_file(
        self,
        source: Path,
        destination: str,
    ) -> None:

        if self.backend == "local":
            await asyncio.to_thread(
                self._save_local,
                source,
                destination,
            )
            return

        await asyncio.to_thread(
            self._upload_s3,
            source,
            destination,
        )

    async def download_file(
        self,
        source: str,
        destination: Path,
    ) -> None:

        destination = Path(destination)

        if self.backend == "local":
            await asyncio.to_thread(
                self._download_local,
                source,
                destination,
            )
            return

        await asyncio.to_thread(
            self._download_s3,
            source,
            destination,
        )

    async def delete_file(
        self,
        destination: str,
    ) -> None:

        if self.backend == "local":
            await asyncio.to_thread(
                self._delete_local,
                destination,
            )
            return

        await asyncio.to_thread(
            self._delete_s3,
            destination,
        )

    async def exists(
        self,
        destination: str,
    ) -> bool:

        if self.backend == "local":
            return await asyncio.to_thread(
                self._exists_local,
                destination,
            )

        return await asyncio.to_thread(
            self._exists_s3,
            destination,
        )

    def local_path(
        self,
        destination: str,
    ) -> Path:

        return self._local_path(destination)

    def _require_s3_client(self) -> Any:
        if self._s3_client is None:
            raise StorageError(
                "s3_client_not_initialized"
            )

        return self._s3_client

    def _local_path(
        self,
        destination: str,
    ) -> Path:

        if self.backend != "local":
            raise StorageError(
                "local_storage_not_configured"
            )

        candidate = (
            self.root / destination
        ).resolve()

        try:
            candidate.relative_to(self.root)

        except ValueError as exc:
            raise StorageError(
                "invalid_storage_path"
            ) from exc

        return candidate

    def _save_local(
        self,
        source: Path,
        destination: str,
    ) -> None:

        target = self._local_path(destination)

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copyfile(
            source,
            target,
        )

    def _download_local(
        self,
        source: str,
        destination: Path,
    ) -> None:

        source_path = self._local_path(source)

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copyfile(
            source_path,
            destination,
        )

    def _delete_local(
        self,
        destination: str,
    ) -> None:

        target = self._local_path(destination)

        target.unlink(
            missing_ok=True
        )

    def _exists_local(
        self,
        destination: str,
    ) -> bool:

        target = self._local_path(destination)

        return target.is_file()

    def _upload_s3(
        self,
        source: Path,
        destination: str,
    ) -> None:

        client = self._require_s3_client()

        client.upload_file(
            str(source),
            self.settings.s3_bucket_name,
            destination,
        )

    def _download_s3(
        self,
        source: str,
        destination: Path,
    ) -> None:

        client = self._require_s3_client()

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        client.download_file(
            self.settings.s3_bucket_name,
            source,
            str(destination),
        )

    def _delete_s3(
        self,
        destination: str,
    ) -> None:

        client = self._require_s3_client()

        client.delete_object(
            Bucket=self.settings.s3_bucket_name,
            Key=destination,
        )

    def _exists_s3(
        self,
        destination: str,
    ) -> bool:

        client = self._require_s3_client()

        try:
            client.head_object(
                Bucket=self.settings.s3_bucket_name,
                Key=destination,
            )

            return True

        except ClientError as exc:
            code = str(
                exc.response
                .get("Error", {})
                .get("Code", "")
            )

            if code in {
                "404",
                "NoSuchKey",
                "NotFound",
            }:
                return False

            raise

    def _ensure_bucket(self) -> None:

        client = self._require_s3_client()

        bucket = self.settings.s3_bucket_name
        region = self.settings.s3_region

        try:
            client.head_bucket(
                Bucket=bucket
            )
            return

        except ClientError as exc:
            code = str(
                exc.response
                .get("Error", {})
                .get("Code", "")
            )

            if code not in {
                "404",
                "NoSuchBucket",
                "NotFound",
            }:
                raise StorageError(
                    f"s3_bucket_check_failed:{code}"
                ) from exc

        create_args: dict[str, Any] = {
            "Bucket": bucket
        }

        if region and region != "us-east-1":
            create_args[
                "CreateBucketConfiguration"
            ] = {
                "LocationConstraint": region
            }

        client.create_bucket(
            **create_args
        )

    async def create_signed_upload_url(
        self,
        destination: str,
        *,
        content_type: str,
        expires_in: int = 300,
    ) -> str:

        if self.backend != "s3":
            raise StorageError(
                "signed_urls_require_s3"
            )

        client = self._require_s3_client()

        return await asyncio.to_thread(
            client.generate_presigned_url,
            "put_object",
            Params={
                "Bucket": (
                    self.settings.s3_bucket_name
                ),
                "Key": destination,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
            HttpMethod="PUT",
        )

    async def create_signed_download_url(
        self,
        source: str,
        *,
        expires_in: int = 300,
    ) -> str:

        if self.backend != "s3":
            raise StorageError(
                "signed_urls_require_s3"
            )

        client = self._require_s3_client()

        return await asyncio.to_thread(
            client.generate_presigned_url,
            "get_object",
            Params={
                "Bucket": (
                    self.settings.s3_bucket_name
                ),
                "Key": source,
            },
            ExpiresIn=expires_in,
        )