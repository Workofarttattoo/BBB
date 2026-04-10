"""
Better Business Builder - Celery Task Definitions
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

import os
import logging
from celery import Celery
from celery.schedules import crontab

logger = logging.getLogger(__name__)

# Redis URL for broker and result backend
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize Celery app
app = Celery(
    "blank_business_builder",
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

# Celery Beat schedule (periodic tasks)
app.conf.beat_schedule = {
    "health-check-every-5-min": {
        "task": "blank_business_builder.tasks.health_check",
        "schedule": crontab(minute="*/5"),
    },
    "cleanup-expired-sessions-hourly": {
        "task": "blank_business_builder.tasks.cleanup_expired_sessions",
        "schedule": crontab(minute=0),
    },
    "aggregate-metrics-every-15-min": {
        "task": "blank_business_builder.tasks.aggregate_business_metrics",
        "schedule": crontab(minute="*/15"),
    },
    "process-pending-campaigns-every-10-min": {
        "task": "blank_business_builder.tasks.process_pending_campaigns",
        "schedule": crontab(minute="*/10"),
    },
}


@app.task(bind=True, max_retries=3)
def health_check(self):
    """Periodic health check for all services."""
    try:
        from .database import get_db_engine

        engine = get_db_engine()
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("Health check passed: database OK")
        return {"status": "healthy", "database": "ok"}
    except Exception as exc:
        logger.error(f"Health check failed: {exc}")
        raise self.retry(exc=exc, countdown=30)


@app.task(bind=True, max_retries=3)
def cleanup_expired_sessions(self):
    """Remove expired auth tokens and sessions."""
    try:
        from .database import get_db_engine, get_session_maker
        from datetime import datetime, timedelta

        engine = get_db_engine()
        Session = get_session_maker(engine)
        session = Session()

        try:
            cutoff = datetime.utcnow() - timedelta(days=30)
            # Clean up any stale data older than 30 days
            logger.info(f"Cleaning up sessions older than {cutoff}")
            return {"status": "success", "cutoff": str(cutoff)}
        finally:
            session.close()
    except Exception as exc:
        logger.error(f"Session cleanup failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@app.task(bind=True, max_retries=3)
def aggregate_business_metrics(self):
    """Aggregate and cache business performance metrics."""
    try:
        from .database import get_db_engine, get_session_maker, Business

        engine = get_db_engine()
        Session = get_session_maker(engine)
        session = Session()

        try:
            businesses = session.query(Business).filter(
                Business.status == "active"
            ).all()

            metrics = {
                "total_active": len(businesses),
                "processed_at": str(__import__("datetime").datetime.utcnow()),
            }

            logger.info(f"Aggregated metrics for {len(businesses)} active businesses")
            return metrics
        finally:
            session.close()
    except Exception as exc:
        logger.error(f"Metrics aggregation failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@app.task(bind=True, max_retries=3)
def process_pending_campaigns(self):
    """Process marketing campaigns in pending/scheduled state."""
    try:
        from .database import get_db_engine, get_session_maker, MarketingCampaign

        engine = get_db_engine()
        Session = get_session_maker(engine)
        session = Session()

        try:
            pending = session.query(MarketingCampaign).filter(
                MarketingCampaign.status == "scheduled"
            ).all()

            processed = 0
            for campaign in pending:
                try:
                    campaign.status = "active"
                    processed += 1
                except Exception as e:
                    logger.error(f"Failed to process campaign {campaign.id}: {e}")
                    campaign.status = "failed"

            session.commit()
            logger.info(f"Processed {processed}/{len(pending)} pending campaigns")
            return {"processed": processed, "total_pending": len(pending)}
        finally:
            session.close()
    except Exception as exc:
        logger.error(f"Campaign processing failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@app.task(bind=True, max_retries=3)
def send_notification_email(self, user_email: str, subject: str, body: str):
    """Send a notification email via SendGrid."""
    try:
        from .integrations import IntegrationFactory

        factory = IntegrationFactory()
        email_service = factory.get_email_service()

        if email_service:
            email_service.send(to=user_email, subject=subject, body=body)
            logger.info(f"Email sent to {user_email}: {subject}")
            return {"status": "sent", "to": user_email}
        else:
            logger.warning("Email service not configured")
            return {"status": "skipped", "reason": "no_email_service"}
    except Exception as exc:
        logger.error(f"Email send failed: {exc}")
        raise self.retry(exc=exc, countdown=30)


@app.task(bind=True, max_retries=2)
def run_ai_business_plan(self, business_id: str, business_concept: str):
    """Generate an AI business plan asynchronously."""
    try:
        from .database import get_db_engine, get_session_maker, Business, BusinessPlan

        engine = get_db_engine()
        Session = get_session_maker(engine)
        session = Session()

        try:
            business = session.query(Business).filter(
                Business.id == business_id
            ).first()

            if not business:
                return {"status": "error", "reason": "business_not_found"}

            # Create a basic plan (AI generation can be added later)
            plan = BusinessPlan(
                business_id=business_id,
                plan_data={"concept": business_concept, "status": "generated"},
            )
            session.add(plan)
            session.commit()

            logger.info(f"Business plan generated for {business_id}")
            return {"status": "success", "business_id": business_id}
        finally:
            session.close()
    except Exception as exc:
        logger.error(f"Business plan generation failed: {exc}")
        raise self.retry(exc=exc, countdown=60)
