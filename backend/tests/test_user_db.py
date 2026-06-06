import uuid

import pytest
from app.core.config import settings
from app.models.user import User
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

# Use the actual database URL from settings
SQLALCHEMY_DATABASE_URL = str(settings.SQLALCHEMY_DATABASE_URI)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    # We don't want to drop everything if we are using the real DB,
    # but for tests it's better to use a transaction and roll back.
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


def test_create_user(db_session):
    email = f"test-{uuid.uuid4()}@example.com"
    hashed_password = "hashedpassword"  # noqa: S105
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.email == email
    assert user.hashed_password == hashed_password
    assert user.full_name == "Test User"
    assert user.is_active is True


def test_unique_email_constraint(db_session):
    email = f"unique-{uuid.uuid4()}@example.com"
    user1 = User(email=email, hashed_password="hashedpassword")  # noqa: S106
    db_session.add(user1)
    db_session.commit()

    user2 = User(email=email, hashed_password="anotherhash")  # noqa: S106
    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()
