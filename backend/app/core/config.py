from typing import Any

from pydantic import AnyHttpUrl, PostgresDsn, RedisDsn, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise Knowledge Assistant (EKA)"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "JSON"  # Options: "JSON", "TEXT"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # BACKEND_CORS_ORIGINS is a JSON-formatted list of strings
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000"]'
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] | str = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str] | str:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json

                return json.loads(v)
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(v)

    # ALLOWED_HOSTS is a JSON-formatted list of strings
    # or a comma-separated list of strings
    # e.g: '["localhost", "127.0.0.1", "web"]'
    ALLOWED_HOSTS: list[str] | str = ["*"]

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_allowed_hosts(cls, v: Any) -> list[str] | str:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json

                return json.loads(v)
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(v)

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"  # noqa: S105
    POSTGRES_DB: str = "eka_db"
    POSTGRES_PORT: int = 5432
    SQLALCHEMY_DATABASE_URI: PostgresDsn | None = None

    # Vector Search
    DEFAULT_VECTOR_DIMENSION: int = 1536  # Default for text-embedding-3-small/large

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None, info: ValidationInfo) -> Any:
        if isinstance(v, str) and v:
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            username=info.data.get("POSTGRES_USER"),
            password=info.data.get("POSTGRES_PASSWORD"),
            host=info.data.get("POSTGRES_SERVER"),
            port=info.data.get("POSTGRES_PORT"),
            path=f"{info.data.get('POSTGRES_DB') or ''}",
        )

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None
    REDIS_DB: int = 0
    REDIS_URL: RedisDsn | None = None

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_connection(cls, v: str | None, info: ValidationInfo) -> Any:
        if isinstance(v, str) and v:
            return v
        return RedisDsn.build(
            scheme="redis",
            host=info.data.get("REDIS_HOST"),
            port=info.data.get("REDIS_PORT"),
            password=info.data.get("REDIS_PASSWORD"),
            path=f"{info.data.get('REDIS_DB') or 0}",
        )

    # AI Models
    OPENAI_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None

    # Storage (MinIO / S3)
    S3_ACCESS_KEY: str | None = None
    S3_SECRET_KEY: str | None = None
    S3_BUCKET: str = "eka-documents"
    S3_REGION: str = "us-east-1"
    S3_ENDPOINT: str | None = None
    S3_USE_SSL: bool = False

    # Rate Limiting
    # Master switch — set RATE_LIMIT_ENABLED=false to disable in tests
    RATE_LIMIT_ENABLED: bool = True
    # Default: 60 requests per 60 seconds (1 req/s burst-tolerant)
    RATE_LIMIT_DEFAULT_REQUESTS: int = 60
    RATE_LIMIT_DEFAULT_WINDOW_SECONDS: int = 60
    # Auth / Login endpoints — stricter to prevent brute-force
    RATE_LIMIT_AUTH_REQUESTS: int = 10
    RATE_LIMIT_AUTH_WINDOW_SECONDS: int = 60

    # Celery
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    @field_validator("CELERY_BROKER_URL", mode="before")
    @classmethod
    def assemble_celery_broker(cls, v: str | None, info: ValidationInfo) -> Any:
        if isinstance(v, str) and v:
            return v
        # Default ke Redis URL jika tidak diset
        redis_url = info.data.get("REDIS_URL")
        return str(redis_url) if redis_url else None

    @field_validator("CELERY_RESULT_BACKEND", mode="before")
    @classmethod
    def assemble_celery_backend(cls, v: str | None, info: ValidationInfo) -> Any:
        if isinstance(v, str) and v:
            return v
        redis_url = info.data.get("REDIS_URL")
        return str(redis_url) if redis_url else None

    # Document Processing
    MAX_UPLOAD_SIZE_MB: int = 50

    model_config = SettingsConfigDict(
        case_sensitive=True, env_file=".env", extra="ignore"
    )


settings = Settings()
