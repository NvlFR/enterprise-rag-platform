"""
Rate Limiting module for the Enterprise Knowledge Assistant (EKA).

Strategy: Redis Sliding Window Counter (Pipeline-based)
- Uses a sorted set (ZSET) per key where each member is a unique request ID
  and the score is the request timestamp in milliseconds.
- Old entries outside the window are pruned on every request (ZREMRANGEBYSCORE).
- Uses a Redis pipeline (MULTI/EXEC) for atomic multi-command execution.
- Compatible with both real Redis and fakeredis (no Lua eval required).

Key format:
  - Per-IP  : ratelimit:ip:<client_ip>:<route_key>
  - Per-User: ratelimit:user:<user_id>:<route_key>

If Redis is unavailable the limiter fails open (allows the request) and logs
a warning, so a Redis outage does not take down the API.
"""

import time
import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.core.logging import get_logger
from app.core.redis import redis_client

logger = get_logger(__name__)


def _build_key(prefix: str, identifier: str, route_key: str) -> str:
    """Build a namespaced Redis key."""
    # Sanitise the identifier so colons cannot break the key structure
    safe_id = identifier.replace(":", "_")
    return f"ratelimit:{prefix}:{safe_id}:{route_key}"


def _check_rate_limit(
    *,
    key: str,
    max_requests: int,
    window_seconds: int,
) -> tuple[int, int]:
    """
    Execute the sliding-window check against Redis using a pipeline.

    Sends ZREMRANGEBYSCORE + ZCARD + ZADD + EXPIRE in a single pipelined
    transaction (MULTI/EXEC) to minimise round-trips.

    Returns:
        ``(current_count, limit)`` — the caller decides whether to raise 429.

    Raises:
        Nothing — on Redis errors the request is allowed through (fail-open).
    """
    if not settings.RATE_LIMIT_ENABLED:
        return 0, max_requests

    try:
        client = redis_client.client
        now_ms = int(time.time() * 1000)
        window_ms = window_seconds * 1000
        cutoff_ms = now_ms - window_ms
        req_id = str(uuid.uuid4())
        # TTL = window + small buffer so the key auto-expires cleanly
        ttl_sec = window_seconds + 10

        pipe = client.pipeline()
        pipe.zremrangebyscore(key, "-inf", cutoff_ms)  # prune expired entries
        pipe.zcard(key)  # count *before* adding current request
        pipe.zadd(key, {req_id: now_ms})  # record current request
        pipe.expire(key, ttl_sec)  # refresh TTL
        results = pipe.execute()

        # results[1] = ZCARD result = count before this request
        count_before = int(results[1])
        current = count_before + 1
        return current, max_requests

    except Exception as exc:  # noqa: BLE001
        logger.warning(
            f"Rate limiter Redis error (fail-open): {exc}",
            extra={"extra_info": {"key": key, "error": str(exc)}},
        )
        return 0, max_requests


# ---------------------------------------------------------------------------
# Public FastAPI dependency factory
# ---------------------------------------------------------------------------

_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token",
    auto_error=False,
)


def rate_limit(
    max_requests: int | None = None,
    window_seconds: int | None = None,
    route_key: str = "default",
    per_user: bool = True,
) -> Callable:
    """
    FastAPI dependency factory that applies sliding-window rate limiting.

    Usage::

        @router.post("/login/access-token")
        def login(
            _: None = Depends(rate_limit(max_requests=10, window_seconds=60,
                                          route_key="auth_login")),
            ...
        ):
            ...

    Args:
        max_requests:    Maximum requests allowed within the window.
                         Defaults to ``settings.RATE_LIMIT_DEFAULT_REQUESTS``.
        window_seconds:  Duration of the sliding window in seconds.
                         Defaults to ``settings.RATE_LIMIT_DEFAULT_WINDOW_SECONDS``.
        route_key:       Logical name for this bucket (e.g. ``"auth_login"``).
                         Different route_keys are tracked independently.
        per_user:        If ``True`` and a valid Bearer token is present the
                         limit is applied per authenticated user; otherwise
                         per client IP.
    """
    _max = (
        max_requests
        if max_requests is not None
        else settings.RATE_LIMIT_DEFAULT_REQUESTS
    )
    _window = (
        window_seconds
        if window_seconds is not None
        else settings.RATE_LIMIT_DEFAULT_WINDOW_SECONDS
    )

    async def _dependency(
        request: Request,
        token: str | None = Depends(_oauth2),  # noqa: B008
    ) -> None:
        if not settings.RATE_LIMIT_ENABLED:
            return

        # --- Determine identifier (user or IP) ---
        identifier: str | None = None

        if per_user and token:
            # Try to extract subject from JWT without full validation here;
            # full auth is still enforced downstream by get_current_user.
            try:
                from jose import jwt  # local import to avoid circular deps

                payload = jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=[settings.ALGORITHM],
                    options={"verify_exp": False},
                )
                sub = payload.get("sub")
                if sub:
                    identifier = f"user:{sub}"
            except Exception as jwt_exc:  # noqa: BLE001
                # Malformed / expired token — fall back to IP-based limiting
                logger.debug(
                    f"Rate limiter JWT decode failed (fallback to IP): {jwt_exc}"
                )

        if identifier is None:
            # Fall back to client IP
            client = request.client
            ip = client.host if client else "unknown"
            # Respect X-Forwarded-For set by trusted proxies / load balancers
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                ip = forwarded_for.split(",")[0].strip()
            identifier = f"ip:{ip}"

        redis_key = _build_key(
            prefix=identifier.split(":")[0],
            identifier=identifier.split(":", 1)[1],
            route_key=route_key,
        )

        current, limit = _check_rate_limit(
            key=redis_key,
            max_requests=_max,
            window_seconds=_window,
        )

        remaining = max(0, limit - current)
        retry_after = _window  # conservative: retry after the full window

        # Inject informational state for RateLimitHeadersMiddleware
        request.state.ratelimit_limit = limit
        request.state.ratelimit_remaining = remaining
        request.state.ratelimit_window = _window

        if current > limit:
            logger.warning(
                f"Rate limit exceeded: key={redis_key} count={current} limit={limit}",
                extra={
                    "extra_info": {
                        "rate_limit_key": redis_key,
                        "count": current,
                        "limit": limit,
                    }
                },
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please slow down.",
                    "limit": limit,
                    "window_seconds": _window,
                    "retry_after": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Window": str(_window),
                },
            )

        logger.debug(
            f"Rate limit check passed: key={redis_key} count={current}/{limit}",
        )

    return _dependency


# ---------------------------------------------------------------------------
# Pre-built dependency instances for common use-cases
# ---------------------------------------------------------------------------

#: Strict limiter for auth endpoints (login) — 10 req / 60 s per IP
auth_rate_limit = rate_limit(
    max_requests=settings.RATE_LIMIT_AUTH_REQUESTS,
    window_seconds=settings.RATE_LIMIT_AUTH_WINDOW_SECONDS,
    route_key="auth_login",
    per_user=False,  # pre-auth endpoint: no user yet
)

#: General API limiter — 60 req / 60 s per authenticated user (or IP)
default_rate_limit = rate_limit(
    max_requests=settings.RATE_LIMIT_DEFAULT_REQUESTS,
    window_seconds=settings.RATE_LIMIT_DEFAULT_WINDOW_SECONDS,
    route_key="default",
    per_user=True,
)
