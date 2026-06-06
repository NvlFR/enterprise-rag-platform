import uuid

import pytest
from app.core import security
from app.core.config import settings
from app.models.enums import UserRole
from app.models.user import User
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture
def admin_user(db: Session) -> User:
    email = f"admin-{uuid.uuid4()}@example.com"
    password = "adminpassword123"  # noqa: S105
    hashed_password = security.get_password_hash(password)
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    user.plain_password = password
    return user


@pytest.fixture
def regular_user(db: Session) -> User:
    email = f"user-{uuid.uuid4()}@example.com"
    password = "userpassword123"  # noqa: S105
    hashed_password = security.get_password_hash(password)
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name="Regular User",
        role=UserRole.USER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    user.plain_password = password
    return user


def get_token_headers(client: TestClient, user: User) -> dict[str, str]:
    login_data = {
        "username": user.email,
        "password": user.plain_password,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    access_token = tokens["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


def test_admin_access_health_admin(client: TestClient, admin_user: User):
    headers = get_token_headers(client, admin_user)
    r = client.get(f"{settings.API_V1_STR}/health/admin", headers=headers)
    assert r.status_code == 200
    assert "Hello Admin" in r.json()["message"]


def test_regular_user_access_health_admin(client: TestClient, regular_user: User):
    headers = get_token_headers(client, regular_user)
    r = client.get(f"{settings.API_V1_STR}/health/admin", headers=headers)
    assert r.status_code == 403
    assert r.json()["detail"] == "The user doesn't have enough privileges"
