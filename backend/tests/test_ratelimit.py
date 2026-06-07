"""
Integration tests for TASK-015: Rate Limiting Implementation.

Strategy:
- Mock `redis_client._client` to use a fakeredis instance for isolation.
- Override FastAPI dependency `auth_rate_limit` directly via app.dependency_overrides
  to set very low limits so we can hit them quickly.
- Verify HTTP 429 response body, headers (Retry-After, X-RateLimit-*).
- Verify that requests within the limit still pass (HTTP 200/400).
- Verify fail-open behaviour when Redis is unavailable.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _exhaust_limit(
    client: TestClient,
    n: int,
    url: str = "/api/v1/login/access-token",
    ip: str | None = None,
):
    """Hit *url* exactly *n* times to exhaust the rate limit."""
    headers = {"X-Forwarded-For": ip} if ip else {}
    for _ in range(n):
        client.post(
            url,
            data={"username": "x@x.com", "password": "bad"},
            headers=headers,
        )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def fake_redis():
    """
    Provide a fakeredis instance in place of the real Redis client.
    Skips if fakeredis is not installed.
    """
    try:
        import fakeredis

        server = fakeredis.FakeServer()
        return fakeredis.FakeRedis(server=server, decode_responses=True)
    except ImportError:
        pytest.skip("fakeredis not installed — skipping Redis-backed tests")


@pytest.fixture()
def rate_limit_client(fake_redis):
    """
    TestClient whose app:
    - Uses a fakeredis backend for rate limiting.
    - Has auth_rate_limit overridden to allow only 3 requests per window.

    We override via app.dependency_overrides so FastAPI resolves the patched
    dep instead of the module-level cached closure.
    """
    from app.core import ratelimit as rl_module
    from app.main import app

    # Build a tight dep (3 req / 60 s) backed by fakeredis
    with patch.object(rl_module.redis_client, "_client", fake_redis):
        tight_dep = rl_module.rate_limit(
            max_requests=3,
            window_seconds=60,
            route_key="auth_login_test",
            per_user=False,
        )

        # Override the cached module-level dep inside the app
        app.dependency_overrides[rl_module.auth_rate_limit] = tight_dep

        with TestClient(app) as c:
            # Keep redis patch active during requests
            with patch.object(rl_module.redis_client, "_client", fake_redis):
                yield c

    app.dependency_overrides.pop(rl_module.auth_rate_limit, None)


# ---------------------------------------------------------------------------
# Unit tests: _check_rate_limit
# ---------------------------------------------------------------------------


class TestCheckRateLimitUnit:
    """Low-level unit tests for the sliding-window pipeline function."""

    def test_within_limit_returns_correct_count(self, fake_redis):
        from app.core import ratelimit as rl_module
        from app.core.config import settings

        with (
            patch.object(settings, "RATE_LIMIT_ENABLED", True),
            patch.object(rl_module.redis_client, "_client", fake_redis),
        ):
            count, limit = rl_module._check_rate_limit(
                key="ratelimit:ip:testhost:unit",
                max_requests=5,
                window_seconds=60,
            )
        assert count == 1
        assert limit == 5

    def test_multiple_requests_increment_counter(self, fake_redis):
        from app.core import ratelimit as rl_module
        from app.core.config import settings

        with (
            patch.object(settings, "RATE_LIMIT_ENABLED", True),
            patch.object(rl_module.redis_client, "_client", fake_redis),
        ):
            for _ in range(3):
                count, limit = rl_module._check_rate_limit(
                    key="ratelimit:ip:counter_test:unit",
                    max_requests=10,
                    window_seconds=60,
                )
        assert count == 3
        assert limit == 10

    def test_disabled_always_returns_zero(self, fake_redis):
        from app.core import ratelimit as rl_module
        from app.core.config import settings

        with patch.object(settings, "RATE_LIMIT_ENABLED", False):
            count, limit = rl_module._check_rate_limit(
                key="ratelimit:ip:disabled:unit",
                max_requests=5,
                window_seconds=60,
            )
        assert count == 0

    def test_redis_error_fails_open(self):
        """When Redis pipeline raises, the limiter must NOT block the request."""
        from app.core import ratelimit as rl_module
        from app.core.config import settings

        # Mock the pipeline object so execute() raises
        bad_pipeline = MagicMock()
        bad_pipeline.execute.side_effect = ConnectionError("Redis down")

        bad_redis = MagicMock()
        bad_redis.pipeline.return_value = bad_pipeline

        with (
            patch.object(settings, "RATE_LIMIT_ENABLED", True),
            patch.object(rl_module.redis_client, "_client", bad_redis),
        ):
            count, limit = rl_module._check_rate_limit(
                key="ratelimit:ip:broken:unit",
                max_requests=5,
                window_seconds=60,
            )
        # Fail-open: count == 0 → request is allowed through
        assert count == 0

    def test_redis_ttl_is_set(self, fake_redis):
        """Keys in Redis should have a TTL so they expire automatically."""
        from app.core import ratelimit as rl_module
        from app.core.config import settings

        key = "ratelimit:ip:ttlcheck:unit"
        with (
            patch.object(settings, "RATE_LIMIT_ENABLED", True),
            patch.object(rl_module.redis_client, "_client", fake_redis),
        ):
            rl_module._check_rate_limit(
                key=key,
                max_requests=5,
                window_seconds=30,
            )
        ttl = fake_redis.ttl(key)
        # TTL = window (30) + buffer (10) = 40, allow a few seconds delta
        assert 30 <= ttl <= 45


# ---------------------------------------------------------------------------
# Integration tests: HTTP layer
# ---------------------------------------------------------------------------


class TestRateLimitHTTP:
    """End-to-end tests hitting the FastAPI app via TestClient."""

    def test_requests_within_limit_succeed(self, rate_limit_client: TestClient):
        """First N requests (within limit=3) must NOT return 429."""
        for _ in range(3):
            r = rate_limit_client.post(
                "/api/v1/login/access-token",
                data={"username": "x@x.com", "password": "bad"},
            )
            assert r.status_code != 429, (
                f"Unexpected 429 before limit reached: {r.json()}"
            )

    def test_exceeding_limit_returns_429(self, rate_limit_client: TestClient):
        """Request N+1 (beyond limit=3) must return HTTP 429."""
        _exhaust_limit(rate_limit_client, 3)

        r = rate_limit_client.post(
            "/api/v1/login/access-token",
            data={"username": "x@x.com", "password": "bad"},
        )
        assert r.status_code == 429

    def test_429_response_body_structure(self, rate_limit_client: TestClient):
        """HTTP 429 response must include the RATE_LIMIT_EXCEEDED error code."""
        _exhaust_limit(rate_limit_client, 3)

        r = rate_limit_client.post(
            "/api/v1/login/access-token",
            data={"username": "x@x.com", "password": "bad"},
        )
        assert r.status_code == 429
        body = r.json()
        assert "error" in body
        error = body["error"]
        assert error.get("code") == "RATE_LIMIT_EXCEEDED"
        assert "limit" in error or "message" in error

    def test_429_response_has_retry_after_header(self, rate_limit_client: TestClient):
        """Retry-After header must be present on HTTP 429."""
        _exhaust_limit(rate_limit_client, 3)

        r = rate_limit_client.post(
            "/api/v1/login/access-token",
            data={"username": "x@x.com", "password": "bad"},
        )
        assert r.status_code == 429
        assert "retry-after" in r.headers

    def test_rate_limit_headers_on_normal_response(self, rate_limit_client: TestClient):
        """Successful (or 400) responses should carry X-RateLimit-* headers."""
        r = rate_limit_client.post(
            "/api/v1/login/access-token",
            data={"username": "x@x.com", "password": "bad"},
        )
        assert r.status_code in (200, 400)
        assert "x-ratelimit-limit" in r.headers
        assert "x-ratelimit-remaining" in r.headers
        assert "x-ratelimit-window" in r.headers

    def test_different_ips_have_independent_counters(
        self, rate_limit_client: TestClient
    ):
        """Rate limits are per-IP — different IPs have independent counters."""
        # Exhaust limit from IP 1
        _exhaust_limit(rate_limit_client, 3, ip="10.0.0.1")

        # IP 1 is now rate-limited
        r_ip1 = rate_limit_client.post(
            "/api/v1/login/access-token",
            data={"username": "x@x.com", "password": "bad"},
            headers={"X-Forwarded-For": "10.0.0.1"},
        )
        assert r_ip1.status_code == 429

        # IP 2 should NOT be rate-limited (fresh counter)
        r_ip2 = rate_limit_client.post(
            "/api/v1/login/access-token",
            data={"username": "x@x.com", "password": "bad"},
            headers={"X-Forwarded-For": "10.0.0.2"},
        )
        assert r_ip2.status_code != 429

    def test_rate_limit_disabled_no_429(self):
        """When RATE_LIMIT_ENABLED=False, no request should ever return 429."""
        from app.core.config import settings
        from app.main import app

        with patch.object(settings, "RATE_LIMIT_ENABLED", False):
            with TestClient(app) as c:
                for _ in range(20):
                    r = c.post(
                        "/api/v1/login/access-token",
                        data={"username": "x@x.com", "password": "bad"},
                    )
                    assert r.status_code != 429


# ---------------------------------------------------------------------------
# Unit tests: key builder
# ---------------------------------------------------------------------------


class TestBuildKey:
    def test_ip_key_format(self):
        from app.core.ratelimit import _build_key

        key = _build_key(prefix="ip", identifier="192.168.1.1", route_key="login")
        assert key == "ratelimit:ip:192.168.1.1:login"

    def test_user_key_format(self):
        from app.core.ratelimit import _build_key

        key = _build_key(prefix="user", identifier="user-uuid-abc", route_key="chat")
        assert key == "ratelimit:user:user-uuid-abc:chat"

    def test_colon_in_identifier_is_sanitised(self):
        from app.core.ratelimit import _build_key

        key = _build_key(prefix="ip", identifier="::1", route_key="test")
        # The body of the key (between prefix and route_key) must have no colons
        body = key.removeprefix("ratelimit:ip:").removesuffix(":test")
        assert ":" not in body
