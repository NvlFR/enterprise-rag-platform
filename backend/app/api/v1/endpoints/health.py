from typing import Any

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", response_model=dict[str, str])
def health_check() -> Any:
    """
    Check the health of the application.
    """
    return {"status": "ok"}
