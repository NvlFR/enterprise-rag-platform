from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.redis import redis_client
from app.db.session import SessionLocal

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/health", response_model=dict[str, str])
def health_check(db: Session = Depends(get_db)) -> Any:  # noqa: B008
    """
    Check the health of the application, including database and redis connectivity.
    """
    health_status = {
        "status": "ok",
        "database": "connected",
        "redis": "connected",
        "vector": "available",
    }
    try:
        # Check database connectivity
        db.execute(text("SELECT 1"))

        # Check for vector extension
        result = db.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        )
        if not result.scalar():
            health_status["vector"] = "missing"
            health_status["status"] = "degraded"

        # Check redis connectivity
        if not redis_client.ping():
            health_status["redis"] = "disconnected"
            health_status["status"] = "degraded"

        if health_status["status"] == "degraded":
            return health_status

        return health_status
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "database": "unknown",
                "redis": "unknown",
                "error": str(e),
            },
        ) from e
