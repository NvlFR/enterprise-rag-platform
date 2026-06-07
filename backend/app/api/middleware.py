import time

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SecurityHeadersMiddleware:
    """
    Middleware to inject basic security headers into all HTTP responses.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: Message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-Frame-Options"] = "DENY"
                headers["X-Content-Type-Options"] = "nosniff"

                # Strict-Transport-Security (HSTS) if in production
                if settings.ENVIRONMENT == "production":
                    headers["Strict-Transport-Security"] = (
                        "max-age=63072000; includeSubDomains; preload"
                    )

                # Basic Content-Security-Policy (CSP)
                headers["Content-Security-Policy"] = (
                    "default-src 'self'; "
                    "img-src 'self' data:; "
                    "style-src 'self' 'unsafe-inline'; "
                    "script-src 'self' 'unsafe-inline';"
                )
                headers["X-XSS-Protection"] = "1; mode=block"
                headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            await send(message)

        await self.app(scope, receive, send_wrapper)


class RequestLoggingMiddleware:
    """
    Middleware to log request details: Method, Path, User Agent, IP, Response Time.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()

        # Extract metadata from scope
        method = scope.get("method", "")
        path = scope.get("path", "")
        query_string = scope.get("query_string", b"").decode("utf-8")

        # Client host info
        client = scope.get("client")
        client_host = client[0] if client else "unknown"

        # User-agent from headers
        user_agent = "unknown"
        for name, value in scope.get("headers", []):
            if name == b"user-agent":
                user_agent = value.decode("utf-8", errors="ignore")
                break

        status_code = [500]  # Default status code if request fails unexpectedly

        async def send_wrapper(message: Message):
            if message["type"] == "http.response.start":
                status_code[0] = message.get("status", 200)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            extra_info = {
                "method": method,
                "path": path,
                "query_params": query_string,
                "client_ip": client_host,
                "user_agent": user_agent,
                "status_code": 500,
                "duration_ms": round(process_time, 2),
                "error": str(e),
            }
            logger.error(
                f"{method} {path} - Failed - "
                f"Duration: {process_time:.2f}ms - Error: {e}",
                extra={"extra_info": extra_info},
            )
            raise e
        else:
            process_time = (time.time() - start_time) * 1000
            extra_info = {
                "method": method,
                "path": path,
                "query_params": query_string,
                "client_ip": client_host,
                "user_agent": user_agent,
                "status_code": status_code[0],
                "duration_ms": round(process_time, 2),
            }
            logger.info(
                f"{method} {path} - Status: {status_code[0]} - "
                f"Duration: {process_time:.2f}ms",
                extra={"extra_info": extra_info},
            )
