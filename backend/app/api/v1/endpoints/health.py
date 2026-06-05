from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

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
    Check the health of the application, including database connectivity.
    """
    try:
        # Check database connectivity
        db.execute(text("SELECT 1"))

        # Check for vector extension
        result = db.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        )
        if not result.scalar():
            return {"status": "degraded", "database": "connected", "vector": "missing"}

        return {"status": "ok", "database": "connected", "vector": "available"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "database": "disconnected", "error": str(e)},
        ) from e
