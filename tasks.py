"""
Better Business Builder - Celery Task Definitions
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

import os
import logging
from celery import Celery

logger = logging.getLogger(__name__)

# Redis URL for broker and result backend
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize Celery app
app = Celery(
    "blank_business_builder_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

# Celery configuration
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minute hard limit
    task_soft_time_limit=240,  # 4 minute soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    result_expires=3600,  # Results expire after 1 hour
)


@app.task(bind=True, max_retries=3)
def process_data(self, data_id: int):
    """Example task to process data."""
    try:
        logger.info(f"Processing data {data_id}")
        return {"status": "success", "data_id": data_id}
    except Exception as exc:
        logger.error(f"Process failed: {exc}")
        raise self.retry(exc=exc, countdown=30)


@app.task(bind=True, max_retries=3)
def send_email_task(self, user_email: str, subject: str, body: str):
    """Example task to send a notification email."""
    try:
        logger.info(f"Email sent to {user_email}: {subject}")
        return {"status": "sent", "to": user_email}
    except Exception as exc:
        logger.error(f"Email send failed: {exc}")
        raise self.retry(exc=exc, countdown=30)
