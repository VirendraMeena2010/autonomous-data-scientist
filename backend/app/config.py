
from pathlib import Path
from typing import Annotated, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import NoDecode


class Settings(BaseSettings):
    # Application
    app_name: str = "Autonomous Data Scientist"
    environment: str = "development"
    api_prefix: str = "/api/v1"

    # CORS
    cors_origins: Annotated[
        tuple[str, ...],
        NoDecode,
    ] = (
        "http://localhost:5173",
        "http://localhost:3000",
        "https://autonomous-data-scientist-two.vercel.app",
    )

    cors_allow_credentials: bool = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            return tuple(
                origin.strip()
                for origin in value.split(",")
                if origin.strip()
            )

        return value

    # Storage
    storage_backend: Literal["local", "s3"] = "local"

    local_storage_path: Path = Path("/data/uploads")

    # S3 / Supabase Storage
    s3_endpoint_url: str = ""
    s3_bucket_name: str = "aidatascientist"
    s3_region: str = "ap-northeast-2"

    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    # Redis
    redis_enabled: bool = False
    redis_url: str = ""

    # Environment configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
