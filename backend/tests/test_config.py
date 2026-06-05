import os
from unittest import mock

import pytest
from app.core.config import Settings
from pydantic import ValidationError
from pydantic_settings.sources import SettingsError


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
            Settings()
