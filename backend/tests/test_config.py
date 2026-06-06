import os
from unittest import mock

import pytest
from app.core.config import Settings
from pydantic import ValidationError
from pydantic_settings import SettingsError


def test_settings_default_values():
    with mock.patch.dict(os.environ, {"SECRET_KEY": "test_secret"}):
        settings = Settings()
        assert settings.PROJECT_NAME == "Enterprise Knowledge Assistant (EKA)"
        assert settings.ENVIRONMENT == "development"
        assert settings.POSTGRES_PORT == 5432
        assert (
            str(settings.SQLALCHEMY_DATABASE_URI)
            == "postgresql://postgres:postgres@localhost:5432/eka_db"
        )
        # Redis defaults
        assert settings.REDIS_HOST == "localhost"
        assert settings.REDIS_PORT == 6379
        assert str(settings.REDIS_URL) == "redis://localhost:6379/0"


def test_redis_settings():
    with mock.patch.dict(
        os.environ,
        {
            "SECRET_KEY": "test_secret",
            "REDIS_HOST": "redis-host",
            "REDIS_PORT": "6380",
            "REDIS_PASSWORD": "password123",  # noqa: S105
            "REDIS_DB": "1",
        },
    ):
        settings = Settings()
        assert settings.REDIS_HOST == "redis-host"
        assert settings.REDIS_PORT == 6380
        assert settings.REDIS_PASSWORD == "password123"  # noqa: S105
        assert settings.REDIS_DB == 1
        assert str(settings.REDIS_URL) == "redis://:password123@redis-host:6380/1"  # noqa: S105


def test_settings_from_env():
    with mock.patch.dict(
        os.environ,
        {
            "SECRET_KEY": "test_secret",
            "PROJECT_NAME": "Test Project",
            "POSTGRES_DB": "test_db",
            "OPENAI_API_KEY": "sk-test",
        },
    ):
        settings = Settings()
        assert settings.PROJECT_NAME == "Test Project"
        assert settings.POSTGRES_DB == "test_db"
        assert settings.OPENAI_API_KEY == "sk-test"
        assert "test_db" in str(settings.SQLALCHEMY_DATABASE_URI)


def test_invalid_cors_origins():
    with mock.patch.dict(
        os.environ, {"SECRET_KEY": "test_secret", "BACKEND_CORS_ORIGINS": "invalid-url"}
    ):
        # pydantic-settings raises SettingsError when it fails to parse the
        # field from environment
        with pytest.raises((ValidationError, SettingsError)):
            Settings()


def test_db_uri_override():
    custom_uri = "postgresql://user:pass@remote:5433/custom_db"
    with mock.patch.dict(
        os.environ, {"SECRET_KEY": "test_secret", "SQLALCHEMY_DATABASE_URI": custom_uri}
    ):
        settings = Settings()
        assert str(settings.SQLALCHEMY_DATABASE_URI) == custom_uri


def test_missing_secret_key():
    with mock.patch.dict(os.environ, {}, clear=True):
        # We need to clear because other env vars might be set in the runner
        # but specifically we want to ensure SECRET_KEY is missing.
        if "SECRET_KEY" in os.environ:
            del os.environ["SECRET_KEY"]
        with pytest.raises(ValidationError):
            # Pass _env_file=None to ensure it doesn't load from .env file
            Settings(_env_file=None)
