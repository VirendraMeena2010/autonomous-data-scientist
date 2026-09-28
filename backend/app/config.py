from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Autonomous Data Scientist"
    environment: Literal["local", "development", "production"] = "development"

    api_prefix: str = "/api/v1"

    database_url: str = ""
    database_pool_size: int = 10
    database_max_overflow: int = 20

    redis_enabled: bool = False
    redis_url: str = "redis://localhost:6379/0"
    background_queue_name: str = "ads:analysis_queue"

    storage_backend: Literal["local", "s3"] = "local"
    local_storage_path: Path = Path("/data/uploads")

    s3_endpoint_url: str = ""
    s3_bucket_name: str = "aidatascientist"
    s3_region: str = "ap-northeast-2"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    model_provider: Literal["openai", "anthropic", "nvidia", "mock"] = "openai"
    model_name: str = "gpt-4o-mini"
    model_temperature: float = 0.2

    openai_api_key: str | None = None
    openai_base_url: str = "https://api.aicredits.in/v1"
    
    anthropic_api_key: str | None = None
    nvidia_api_key: str | None = None

    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: str | None = None
    bootstrap_admin_name: str = "Admin"

    rate_limit_enabled: bool = True
    rate_limit_default_per_minute: int = 60
    rate_limit_auth_per_minute: int = 10
    rate_limit_upload_per_minute: int = 5

    langfuse_enabled: bool = False
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    nemo_guardrails_enabled: bool = False
    nemo_guardrails_config_dir: Path = Path("guardrails")

    cors_origins: Annotated[
        tuple[str, ...],
        NoDecode,
    ] = Field(
        default_factory=lambda: (
            "http://localhost:5173",
            "http://localhost:3000",
        )
    )

    max_upload_bytes: int = 100 * 1024 * 1024

    allowed_dataset_extensions: tuple[str, ...] = Field(
        default_factory=lambda: (
            ".csv",
            ".parquet",
            ".json",
            ".jsonl",
        )
    )

    antivirus_enabled: bool = False
    antivirus_host: str = "clamav"
    antivirus_port: int = 3310
    antivirus_timeout_seconds: int = 30

    worker_concurrency: int = 1
    analysis_timeout_seconds: int = 1800

    auth_secret_key: str = "dev-secret-change-me"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("api_prefix")
    @classmethod
    def normalize_api_prefix(cls, value: str) -> str:
        value = value.strip()
        if value in {"", "/"}:
            return ""
        return value.rstrip("/")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> tuple[str, ...]:
        if isinstance(value, str):
            return tuple(item.strip() for item in value.split(",") if item.strip())
        if isinstance(value, (list, tuple, set)):
            return tuple(str(item).strip() for item in value if str(item).strip())
        return value  # type: ignore[return-value]

    @field_validator("allowed_dataset_extensions", mode="before")
    @classmethod
    def parse_dataset_extensions(cls, value: object) -> tuple[str, ...]:
        if isinstance(value, str):
            return tuple(item.strip().lower() for item in value.split(",") if item.strip())
        if isinstance(value, (list, tuple, set)):
            return tuple(str(item).strip().lower() for item in value if str(item).strip())
        return value  # type: ignore[return-value]

    @field_validator("auth_secret_key")
    @classmethod
    def validate_auth_secret_key(
        cls,
        value: str,
        info: ValidationInfo,
    ) -> str:
        if info.data.get("environment") == "production" and (
            not value or value == "dev-secret-change-me" or len(value) < 32
        ):
            raise ValueError("AUTH_SECRET_KEY must be at least 32 chars in production")
        return value

    @property
    def langfuse_is_configured(self) -> bool:
        return bool(
            self.langfuse_enabled
            and self.langfuse_public_key
            and self.langfuse_secret_key
        )

    @property
    def cors_origins_list(self) -> list[str]:
        return list(self.cors_origins)

    @property
    def nemo_guardrails_config_exists(self) -> bool:
        return self.nemo_guardrails_config_dir.exists()


settings = Settings()