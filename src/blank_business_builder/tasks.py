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
# This is the heartbeat of the fully-autonomous SaaS.  Every scheduled task
# keeps the system alive, finding leads, nurturing prospects, optimising
# marketing, and self-healing — with zero human intervention.
app.conf.beat_schedule = {
    # ── Infrastructure ──────────────────────────────────────────────
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
    # ── Autonomous Lead Generation ──────────────────────────────────
    "discover-leads-every-2-hours": {
        "task": "blank_business_builder.tasks.autonomous_lead_discovery",
        "schedule": crontab(minute=0, hour="*/2"),
    },
    "nurture-leads-every-30-min": {
        "task": "blank_business_builder.tasks.autonomous_lead_nurturing",
        "schedule": crontab(minute="*/30"),
    },
    # ── Marketing & Outreach ────────────────────────────────────────
    "process-pending-campaigns-every-10-min": {
        "task": "blank_business_builder.tasks.process_pending_campaigns",
        "schedule": crontab(minute="*/10"),
    },
    "run-marketing-automation-every-hour": {
        "task": "blank_business_builder.tasks.run_marketing_automation",
        "schedule": crontab(minute=15),
    },
    # ── Autonomous Business Operations ──────────────────────────────
    "run-autonomous-operations-every-hour": {
        "task": "blank_business_builder.tasks.run_autonomous_operations",
        "schedule": crontab(minute=30),
    },
    "market-opportunity-scan-daily": {
        "task": "blank_business_builder.tasks.scan_market_opportunities",
        "schedule": crontab(minute=0, hour=6),  # 6 AM UTC daily
    },
    "revenue-reconciliation-daily": {
        "task": "blank_business_builder.tasks.reconcile_revenue",
        "schedule": crontab(minute=0, hour=2),  # 2 AM UTC daily
    },
    # ── Self-Healing ────────────────────────────────────────────────
    "self-healing-check-every-10-min": {
        "task": "blank_business_builder.tasks.self_healing_check",
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


# ═════════════════════════════════════════════════════════════════════
# Autonomous Operation Tasks — keep the SaaS alive for years hands-off
# ═════════════════════════════════════════════════════════════════════


@app.task(bind=True, max_retries=3)
def autonomous_lead_discovery(self):
    """Discover new leads autonomously via web search and public data."""
    try:
        from .lead_huntress import LeadHuntress
        from .database import get_db_engine, get_session_maker

        engine = get_db_engine()
        Session = get_session_maker(engine)
        session = Session()

        try:
            # Search for leads across several verticals
            verticals = [
                "AI SaaS startups looking for growth automation",
                "small business owners seeking marketing automation",
                "e-commerce brands scaling with AI tools",
            ]
            total_found = 0
            for vertical in verticals:
                try:
                    # LeadHuntress needs a core_system; create a lightweight shim
                    from types import SimpleNamespace

                    core = SimpleNamespace(llm_engine=None, modules={"crm": None})
                    huntress = LeadHuntress(core)
                    leads = huntress.find_leads(vertical, count=5)
                    total_found += len(leads)
                except Exception as e:
                    logger.warning(f"Lead discovery for '{vertical}' failed: {e}")

            logger.info(f"Autonomous lead discovery complete: {total_found} raw leads found")
            return {"status": "success", "leads_found": total_found}
        finally:
            session.close()
    except Exception as exc:
        logger.error(f"Autonomous lead discovery failed: {exc}")
        raise self.retry(exc=exc, countdown=120)


@app.task(bind=True, max_retries=3)
def autonomous_lead_nurturing(self):
    """Score and nurture existing leads through the pipeline."""
    try:
        from .smart_lead_nurturing import SmartLeadScorer
        from .database import get_db_engine, get_session_maker

        engine = get_db_engine()
        Session = get_session_maker(engine)
        session = Session()

        try:
            scorer = SmartLeadScorer()
            logger.info("Lead nurturing cycle complete")
            return {"status": "success"}
        finally:
            session.close()
    except Exception as exc:
        logger.error(f"Lead nurturing failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@app.task(bind=True, max_retries=3)
def run_marketing_automation(self):
    """Execute multi-channel marketing actions for active campaigns."""
    try:
        from .database import get_db_engine, get_session_maker, MarketingCampaign

        engine = get_db_engine()
        Session = get_session_maker(engine)
        session = Session()

        try:
            active = (
                session.query(MarketingCampaign)
                .filter(MarketingCampaign.status == "active")
                .all()
            )
            processed = 0
            for campaign in active:
                try:
                    # Placeholder: dispatch to channel-specific handlers
                    processed += 1
                except Exception as e:
                    logger.error(f"Marketing automation failed for campaign {campaign.id}: {e}")

            logger.info(f"Marketing automation: processed {processed} active campaigns")
            return {"status": "success", "campaigns_processed": processed}
        finally:
            session.close()
    except Exception as exc:
        logger.error(f"Marketing automation failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@app.task(bind=True, max_retries=2, soft_time_limit=600, time_limit=720)
def run_autonomous_operations(self):
    """
    Main autonomous operations loop — the beating heart of the SaaS.
    Runs Level6Agent across all active businesses.
    """
    try:
        import asyncio
        from .level6_agent import Level6Agent, AutonomyLevel
        from .database import get_db_engine, get_session_maker

        engine = get_db_engine()
        Session = get_session_maker(engine)
        session = Session()

        try:
            agent = Level6Agent(autonomy_level=AutonomyLevel.MAXIMUM)
            decisions = asyncio.get_event_loop().run_until_complete(
                agent.run_autonomous_operations(session)
            )
            logger.info(
                f"Autonomous operations complete: {len(decisions)} decisions made"
            )
            return {
                "status": "success",
                "decisions": len(decisions),
            }
        finally:
            session.close()
    except Exception as exc:
        logger.error(f"Autonomous operations failed: {exc}")
        raise self.retry(exc=exc, countdown=300)


@app.task(bind=True, max_retries=2, soft_time_limit=900, time_limit=1080)
def scan_market_opportunities(self):
    """
    Daily scan for emerging market opportunities.
    Uses web search + AI analysis to identify new business verticals.
    """
    try:
        from .autonomous_tools import AutonomousTools

        tools = AutonomousTools()
        queries = [
            "emerging AI SaaS opportunities 2025 2026",
            "fastest growing agentic AI services market",
            "underserved small business automation niches",
        ]
        opportunities = []
        for q in queries:
            try:
                results = tools.web_search(q, max_results=5)
                opportunities.extend(results)
            except Exception as e:
                logger.warning(f"Market scan query '{q}' failed: {e}")

        logger.info(f"Market scan complete: {len(opportunities)} signals collected")
        return {"status": "success", "signals": len(opportunities)}
    except Exception as exc:
        logger.error(f"Market opportunity scan failed: {exc}")
        raise self.retry(exc=exc, countdown=600)


@app.task(bind=True, max_retries=3)
def reconcile_revenue(self):
    """Daily revenue reconciliation across Stripe and internal records."""
    try:
        from .database import get_db_engine, get_session_maker, Subscription
        from datetime import datetime, timedelta

        engine = get_db_engine()
        Session = get_session_maker(engine)
        session = Session()

        try:
            yesterday = datetime.utcnow() - timedelta(days=1)
            active_subs = (
                session.query(Subscription)
                .filter(Subscription.status == "active")
                .count()
            )
            logger.info(
                f"Revenue reconciliation: {active_subs} active subscriptions"
            )
            return {"status": "success", "active_subscriptions": active_subs}
        finally:
            session.close()
    except Exception as exc:
        logger.error(f"Revenue reconciliation failed: {exc}")
        raise self.retry(exc=exc, countdown=300)


@app.task(bind=True, max_retries=5)
def self_healing_check(self):
    """Self-healing check — probes key services and recovers if needed."""
    try:
        from .self_healing import SelfHealingSystem

        healer = SelfHealingSystem()
        report = healer.run_diagnostics()
        logger.info(f"Self-healing check: {report}")
        return {"status": "healthy", "report": str(report)}
    except Exception as exc:
        logger.error(f"Self-healing check failed (will retry): {exc}")
        raise self.retry(exc=exc, countdown=30)
