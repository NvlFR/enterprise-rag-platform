import pytest
from app.core.security import get_password_hash, verify_password
from app.schemas.user import UserCreate, UserOut
from pydantic import ValidationError


def test_password_hashing():
    password = "secretpassword123"  # noqa: S105
    hashed_password = get_password_hash(password)
    assert hashed_password != password
    assert verify_password(password, hashed_password) is True
    assert verify_password("wrongpassword", hashed_password) is False


def test_user_create_schema():
    # Valid data
    user_in = {
        "email": "test@example.com",
        "password": "strongpassword123",
        "full_name": "Test User",
    }
    user_schema = UserCreate(**user_in)
    assert user_schema.email == "test@example.com"
    assert user_schema.password == "strongpassword123"  # noqa: S105
    assert user_schema.full_name == "Test User"
    assert user_schema.is_active is True
    assert user_schema.role == "user"

    # Invalid email
    with pytest.raises(ValidationError):
        UserCreate(email="invalid-email", password="strongpassword123")  # noqa: S106

    # Password too short
    with pytest.raises(ValidationError):
        UserCreate(email="test@example.com", password="short")  # noqa: S106


def test_user_out_schema():
    import uuid
    from datetime import datetime

    user_data = {
        "id": uuid.uuid4(),
        "email": "test@example.com",
        "full_name": "Test User",
        "is_active": True,
        "role": "user",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    user_out = UserOut(**user_data)
    assert user_out.email == "test@example.com"
    assert isinstance(user_out.id, uuid.UUID)
