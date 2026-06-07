import uuid

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.datastructures import MutableHeaders
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.api.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import get_logger, request_id_var, setup_logging

# Setup logging
setup_logging()
logger = get_logger(__name__)


class RequestIDMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = None
        for name, value in scope.get("headers", []):
            if name == b"x-request-id":
                request_id = value.decode()
                break

        if not request_id:
            request_id = str(uuid.uuid4())

        scope["request_id"] = request_id
        token = request_id_var.set(request_id)

        async def send_wrapper(message: Message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.append("X-Request-ID", request_id)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            request_id_var.reset(token)


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)


class RateLimitHeadersMiddleware:
    """
    Inject X-RateLimit-* informational headers gathered by the rate-limit
    dependency into every HTTP response.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)

        async def send_wrapper(message: Message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                limit = getattr(request.state, "ratelimit_limit", None)
                remaining = getattr(request.state, "ratelimit_remaining", None)
                window = getattr(request.state, "ratelimit_window", None)
                if limit is not None:
                    headers["X-RateLimit-Limit"] = str(limit)
                    headers["X-RateLimit-Remaining"] = str(remaining)
                    headers["X-RateLimit-Window"] = str(window)
            await send(message)

        await self.app(scope, receive, send_wrapper)


# Core Middleware registration
# Middlewares are executed in reverse order of addition (LIFO).
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestIDMiddleware)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin).rstrip("/") for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

if settings.ALLOWED_HOSTS:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[str(host) for host in settings.ALLOWED_HOSTS],
    )


# Global Exception Handlers


@app.exception_handler(AppError)
async def app_exception_handler(request: Request, exc: AppError):
    request_id = request.scope.get("request_id", "")
    token = request_id_var.set(request_id)
    try:
        logger.error(
            f"AppError: {exc.message}",
            extra={"extra_info": {"code": exc.code, "details": exc.details}},
        )
    finally:
        request_id_var.reset(token)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTPException including HTTP 429 from rate limiter."""
    if exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        request_id = request.scope.get("request_id", "")
        token = request_id_var.set(request_id)
        try:
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "extra_info": {
                        "path": request.url.path,
                        "client": str(request.client),
                        "detail": exc.detail,
                    }
                },
            )
        finally:
            request_id_var.reset(token)

        detail = exc.detail if isinstance(exc.detail, dict) else {"message": exc.detail}
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"error": {"code": "RATE_LIMIT_EXCEEDED", **detail}},
            headers=dict(exc.headers) if exc.headers else {},
        )

    # Re-raise all other HTTPExceptions as their default JSON response
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=dict(exc.headers) if exc.headers else {},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    request_id = request.scope.get("request_id", "")
    token = request_id_var.set(request_id)
    try:
        logger.exception("Unhandled exception occurred")
    finally:
        request_id_var.reset(token)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred.",
            }
        },
    )


app.include_router(api_router, prefix=settings.API_V1_STR)
