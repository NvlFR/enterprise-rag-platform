import uuid

from app.core.exceptions import EntityNotFoundError
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app, raise_server_exceptions=False)


# Helper route to trigger an unhandled exception
@app.get("/test-unhandled-exception")
async def trigger_unhandled_exception():
    raise ValueError("Test unhandled exception")


# Helper route to trigger a custom exception
@app.get("/test-custom-exception")
async def trigger_custom_exception():
    raise EntityNotFoundError(entity_name="User", entity_id="123")


def test_request_id_in_header():
    """
    Verify that X-Request-ID is generated and returned in the response headers.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    # Verify it's a valid UUID
    val = response.headers["X-Request-ID"]
    uuid.UUID(val)


def test_provided_request_id_in_header():
    """
    Verify that X-Request-ID provided in the request is returned
    in the response headers.
    """
    request_id = str(uuid.uuid4())
    response = client.get("/api/v1/health", headers={"X-Request-ID": request_id})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id


def test_unhandled_exception_format():
    """
    Verify that unhandled exceptions return a 500 status code
    and the standard error format.
    """
    response = client.get("/test-unhandled-exception")
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert data["error"]["message"] == "An unexpected error occurred."


def test_custom_exception_format():
    """
    Verify that custom exceptions return the correct status code
    and the standard error format.
    """
    response = client.get("/test-custom-exception")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "User with id 123 not found" in data["error"]["message"]
    assert data["error"]["details"] == {"entity": "User", "id": "123"}
