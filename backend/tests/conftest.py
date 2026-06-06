from collections.abc import Generator

import pytest
from app.api import deps
from app.core.config import settings
from app.db.base_class import Base
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    yield
    # We could drop tables here, but often we keep them for analysis


@pytest.fixture(scope="function")
def db() -> Generator:
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Override get_db dependency
    def override_get_db():
        yield session

    app.dependency_overrides[deps.get_db] = override_get_db

    yield session

    session.close()
    transaction.rollback()
    connection.close()
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c
