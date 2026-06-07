from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "eka_worker",
    broker=str(settings.REDIS_URL),
    backend=str(settings.REDIS_URL),
    include=["app.tasks.document"],
)

# Konfigurasi Celery
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Retry policy
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Concurrency dan prefetch
    worker_prefetch_multiplier=1,
    # Result expiry: simpan hasil task selama 24 jam
    result_expires=86400,
    # Task time limits
    task_soft_time_limit=300,  # 5 menit soft limit
    task_time_limit=360,  # 6 menit hard limit
    # Retry dengan exponential backoff default
    task_default_retry_delay=30,
    task_max_retries=3,
)
