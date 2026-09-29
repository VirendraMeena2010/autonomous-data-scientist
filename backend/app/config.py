
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ---------------------------------------------------------
    # Application
    # ---------------------------------------------------------
    app_name: str = "Autonomous Data Scientist"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    database_url: str
    # ---------------------------------------------------------
    # CORS
    # ---------------------------------------------------------
    cors_origins: str = (
        "http://localhost:5173,"
        "http://localhost:3000,"
        "https://autonomous-data-scientist-two.vercel.app"
    )

    cors_allow_credentials: bool = True

    @property
    def cors_origins_list(self) -> tuple[str, ...]:
        return tuple(
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        )

    # ---------------------------------------------------------
    # Storage
    # ---------------------------------------------------------
    storage_backend: Literal["local", "s3"] = "local"

    local_storage_path: Path = Path("/data/uploads")

    # ---------------------------------------------------------
    # S3 / Supabase Storage
    # ---------------------------------------------------------
    s3_endpoint_url: str = ""
    s3_bucket_name: str = "aidatascientist"
    s3_region: str = "ap-northeast-2"

    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    # ---------------------------------------------------------
    # Redis
    # ---------------------------------------------------------
    redis_enabled: bool = False
    redis_url: str = ""

    # ---------------------------------------------------------
    # Environment configuration
    # ---------------------------------------------------------
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
