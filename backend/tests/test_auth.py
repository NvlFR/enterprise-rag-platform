import uuid

import pytest
from app.core import security
from app.core.config import settings
from app.models.user import User
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture
def test_user(db: Session) -> User:
    email = f"test-{uuid.uuid4()}@example.com"
    password = "testpassword123"  # noqa: S105
    hashed_password = security.get_password_hash(password)
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name="Test User",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    user.plain_password = password
    return user


def test_login_access_token(client: TestClient, test_user: User):
    login_data = {
        "username": test_user.email,
        "password": test_user.plain_password,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 200
    tokens = r.json()
    assert "access_token" in tokens
    assert tokens["token_type"] == "bearer"  # noqa: S105


def test_login_incorrect_password(client: TestClient, test_user: User):
    login_data = {
        "username": test_user.email,
        "password": "wrongpassword",
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 400
    assert r.json()["detail"] == "Incorrect email or password"


def test_test_token(client: TestClient, test_user: User):
    login_data = {
        "username": test_user.email,
        "password": test_user.plain_password,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    access_token = tokens["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    r = client.post(f"{settings.API_V1_STR}/login/test-token", headers=headers)
    assert r.status_code == 200
    result = r.json()
    assert result["email"] == test_user.email


def test_test_token_invalid(client: TestClient, test_user: User):
    headers = {"Authorization": "Bearer invalidtoken"}
    r = client.post(f"{settings.API_V1_STR}/login/test-token", headers=headers)
    assert r.status_code == 403
    assert r.json()["detail"] == "Could not validate credentials"
