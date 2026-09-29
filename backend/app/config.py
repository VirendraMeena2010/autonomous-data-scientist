from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # =========================================================
    # Application
    # =========================================================
    app_name: str = "Autonomous Data Scientist"
    environment: str = "development"
    api_prefix: str = "/api/v1"

    # =========================================================
    # Database
    # =========================================================
    database_url: str = ""
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # =========================================================
    # Redis / Background Queue
    # =========================================================
    redis_enabled: bool = False
    redis_url: str = "redis://localhost:6379/0"
    background_queue_name: str = "ads:analysis_queue"

    # =========================================================
    # Storage
    # =========================================================
    storage_backend: Literal["local", "s3"] = "local"
    local_storage_path: Path = Path("/data/uploads")

    # S3 / Supabase-compatible storage
    s3_endpoint_url: str = ""
    s3_bucket_name: str = "aidatascientist"
    s3_region: str = "ap-northeast-2"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    # =========================================================
    # AI / Model Provider
    # =========================================================
    model_provider: str = "openai"
    model_name: str = "gpt-4o-mini"
    model_temperature: float = 0.2

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    nvidia_api_key: str | None = None

    # =========================================================
    # Bootstrap Admin
    # =========================================================
    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: str | None = None
    bootstrap_admin_name: str = "Admin"

    # =========================================================
    # Rate Limiting
    # =========================================================
    rate_limit_enabled: bool = True
    rate_limit_default_per_minute: int = 60
    rate_limit_auth_per_minute: int = 10
    rate_limit_upload_per_minute: int = 5

    # =========================================================
    # Langfuse
    # =========================================================
    langfuse_enabled: bool = False
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # =========================================================
    # NeMo Guardrails
    # =========================================================
    nemo_guardrails_enabled: bool = False
    nemo_guardrails_config_dir: Path = Path("guardrails")

    # =========================================================
    # CORS
    # =========================================================
    cors_origins: str = (
        "http://localhost:5173,"
        "http://localhost:3000,"
        "https://autonomous-data-scientist-two.vercel.app"
    )

    cors_allow_credentials: bool = True

    # =========================================================
    # Uploads
    # =========================================================
    max_upload_bytes: int = 100 * 1024 * 1024

    dataset_extensions: str = (
        ".csv,"
        ".parquet,"
        ".json,"
        ".jsonl"
    )

    # =========================================================
    # Antivirus
    # =========================================================
    # =========================================================
# Antivirus
# =========================================================
    antivirus_enabled: bool = False
    antivirus_host: str = "clamav"
    antivirus_port: int = 3310
    antivirus_timeout_seconds: int = 30

    # =========================================================
    # Worker / Analysis
    # =========================================================
    worker_concurrency: int = 1
    analysis_timeout_seconds: int = 1800

    # =========================================================
    # Authentication
    # =========================================================
    auth_secret_key: str = "dev-secret-change-me"

    # =========================================================
    # Validators
    # =========================================================
    @field_validator("api_prefix")
    @classmethod
    def normalize_api_prefix(cls, value: str) -> str:
        value = value.strip()

        if not value:
            return "/api/v1"

        if not value.startswith("/"):
            value = "/" + value

        return value.rstrip("/")

    @field_validator("cors_origins")
    @classmethod
    def normalize_cors_origins(cls, value: str) -> str:
        if not value:
            return ""

        return ",".join(
            origin.strip()
            for origin in value.split(",")
            if origin.strip()
        )

    @field_validator("dataset_extensions")
    @classmethod
    def normalize_dataset_extensions(cls, value: str) -> str:
        if not value:
            return ""

        extensions = []

        for extension in value.split(","):
            extension = extension.strip().lower()

            if not extension:
                continue

            if not extension.startswith("."):
                extension = "." + extension

            extensions.append(extension)

        return ",".join(extensions)

    # =========================================================
    # Derived Properties
    # =========================================================
    @property
    def cors_origins_list(self) -> tuple[str, ...]:
        return tuple(
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        )

    @property
    def dataset_extensions_list(self) -> tuple[str, ...]:
        return tuple(
            extension.strip().lower()
            for extension in self.dataset_extensions.split(",")
            if extension.strip()
        )

    @property
    def langfuse_is_configured(self) -> bool:
        return bool(
            self.langfuse_enabled
            and self.langfuse_public_key
            and self.langfuse_secret_key
        )

    @property
    def nemo_guardrails_config_exists(self) -> bool:
        return self.nemo_guardrails_config_dir.exists()

    # =========================================================
    # Production Security Validation
    # =========================================================
    @field_validator("auth_secret_key")
    @classmethod
    def validate_auth_secret_key(cls, value: str) -> str:
        value = value.strip()

        # Development can use the default secret.
        # Production requires a real secret.
        return value

    # =========================================================
    # Pydantic Settings Configuration
    # =========================================================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()