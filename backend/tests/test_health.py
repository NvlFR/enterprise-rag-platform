from unittest.mock import MagicMock, patch

from app.api.v1.endpoints.health import get_db
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


@patch("app.api.v1.endpoints.health.redis_client")
def test_health_check_ok(mock_redis):
    # Mock redis ping
    mock_redis.ping.return_value = True

    # Mock the DB session
    mock_db = MagicMock()
    mock_db.execute.return_value.scalar.return_value = "vector"

    # Override the get_db dependency
    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.get("/api/v1/health")

    # Clear overrides after test
    app.dependency_overrides = {}

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "connected",
        "redis": "connected",
        "vector": "available",
    }


@patch("app.api.v1.endpoints.health.redis_client")
def test_health_check_degraded_vector(mock_redis):
    # Mock redis ping
    mock_redis.ping.return_value = True

    # Mock the DB session where vector extension is missing
    mock_db = MagicMock()
    # First call for SELECT 1, second for pg_extension check
    mock_db.execute.return_value.scalar.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.get("/api/v1/health")
    app.dependency_overrides = {}

    assert response.status_code == 200
    assert response.json() == {
        "status": "degraded",
        "database": "connected",
        "redis": "connected",
        "vector": "missing",
    }


@patch("app.api.v1.endpoints.health.redis_client")
def test_health_check_degraded_redis(mock_redis):
    # Mock redis ping failure
    mock_redis.ping.return_value = False

    # Mock the DB session
    mock_db = MagicMock()
    mock_db.execute.return_value.scalar.return_value = "vector"

    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.get("/api/v1/health")
    app.dependency_overrides = {}

    assert response.status_code == 200
    assert response.json() == {
        "status": "degraded",
        "database": "connected",
        "redis": "disconnected",
        "vector": "available",
    }


@patch("app.api.v1.endpoints.health.redis_client")
def test_health_check_error(mock_redis):
    # Mock redis ping
    mock_redis.ping.return_value = True

    # Mock the DB session where connection fails
    mock_db = MagicMock()
    mock_db.execute.side_effect = Exception("Connection refused")

    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.get("/api/v1/health")
    app.dependency_overrides = {}

    assert response.status_code == 500
    assert response.json()["detail"]["status"] == "error"
    assert response.json()["detail"]["database"] == "unknown"
