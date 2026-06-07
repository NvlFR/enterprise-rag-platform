from unittest.mock import patch

from app.core.config import settings
from app.main import app
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.trustedhost import TrustedHostMiddleware


def test_security_headers():
    client = TestClient(app)
    response = client.get("/api/v1/non-existent-route")

    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert "default-src 'self'" in response.headers.get("Content-Security-Policy", "")
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    # STS should not be present in development by default
    assert "Strict-Transport-Security" not in response.headers


def test_security_headers_production():
    with patch.object(settings, "ENVIRONMENT", "production"):
        client = TestClient(app)
        response = client.get("/api/v1/non-existent-route")
        assert (
            response.headers.get("Strict-Transport-Security")
            == "max-age=63072000; includeSubDomains; preload"
        )


def test_cors_headers_allowed():
    client = TestClient(app)
    headers = {"Origin": "http://localhost:3000"}
    response = client.get("/api/v1/non-existent-route", headers=headers)
    assert (
        response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"
    )


def test_cors_headers_disallowed():
    client = TestClient(app)
    headers = {"Origin": "http://evil.com"}
    response = client.get("/api/v1/non-existent-route", headers=headers)
    assert response.headers.get("Access-Control-Allow-Origin") is None


def test_trusted_host_middleware_behavior():
    test_app = FastAPI()
    test_app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["allowed.com", "*.allowed.com"]
    )

    @test_app.get("/")
    def read_root():
        return {"hello": "world"}

    client = TestClient(test_app)

    # Allowed host
    res = client.get("/", headers={"Host": "allowed.com"})
    assert res.status_code == 200

    # Wildcard allowed host
    res = client.get("/", headers={"Host": "sub.allowed.com"})
    assert res.status_code == 200

    # Disallowed host
    res = client.get("/", headers={"Host": "evil.com"})
    assert res.status_code == 400


def test_global_app_trusted_hosts():
    client = TestClient(app)
    response = client.get("/api/v1/non-existent-route")
    assert response.status_code != 400


@patch("app.api.middleware.logger")
def test_request_logging(mock_logger):
    client = TestClient(app)
    client.get("/api/v1/non-existent-route")

    assert mock_logger.info.called
    args, kwargs = mock_logger.info.call_args
    log_msg = args[0]
    assert "GET" in log_msg
    assert "/api/v1/non-existent-route" in log_msg
    assert "extra" in kwargs
    assert "extra_info" in kwargs["extra"]
    extra = kwargs["extra"]["extra_info"]
    assert extra["method"] == "GET"
    assert extra["path"] == "/api/v1/non-existent-route"
    assert extra["status_code"] == 404
    assert "duration_ms" in extra
