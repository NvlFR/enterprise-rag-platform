"""
Celery Worker entrypoint.

Jalankan dengan:
    celery -A app.worker.celery_app worker --loglevel=info

Atau menggunakan Makefile:
    make worker
"""

from app.core.celery_app import celery_app
from app.core.logging import setup_logging

# Setup structured logging untuk worker
setup_logging()

# Re-export agar `celery -A app.worker.celery_app` bisa menemukan instance
__all__ = ["celery_app"]
