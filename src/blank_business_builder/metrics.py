"""
Better Business Builder - Prometheus Metrics
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST  # type: ignore
except ImportError:  # pragma: no cover
    class _MetricStub:
        def __init__(self, *args, **kwargs):
            pass

        def labels(self, *args, **kwargs):
            return self

        def inc(self, *args, **kwargs):
            pass

        def observe(self, *args, **kwargs):
            pass

    def generate_latest(registry=None):  # type: ignore
        return b''

    CONTENT_TYPE_LATEST = 'text/plain; charset=utf-8'
    Counter = Histogram = Gauge = _MetricStub  # type: ignore
from fastapi import Response, Request
from typing import Callable
import time

# Define metrics
requests_total = Counter(
    'bbb_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'bbb_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

active_businesses = Gauge(
    'bbb_active_businesses',
    'Number of active businesses'
)

agent_tasks_total = Counter(
    'bbb_agent_tasks_total',
    'Total agent tasks',
    ['agent_role', 'status']
)

revenue_total = Gauge(
    'bbb_revenue_total',
    'Total revenue generated in USD'
)

database_connections = Gauge(
    'bbb_database_connections',
    'Number of active database connections'
)

cache_hits = Counter(
    'bbb_cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses = Counter(
    'bbb_cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

ai_requests = Counter(
    'bbb_ai_requests_total',
    'Total AI API requests',
    ['service', 'status']
)

ai_request_duration = Histogram(
    'bbb_ai_request_duration_seconds',
    'AI API request duration in seconds',
    ['service']
)

payment_transactions = Counter(
    'bbb_payment_transactions_total',
    'Total payment transactions',
    ['status']
)

subscription_changes = Counter(
    'bbb_subscription_changes_total',
    'Total subscription changes',
    ['plan', 'action']
)

email_campaigns = Counter(
    'bbb_email_campaigns_total',
    'Total email campaigns sent',
    ['status']
)

social_posts = Counter(
    'bbb_social_posts_total',
    'Total social media posts',
    ['platform', 'status']
)


def metrics_endpoint():
    """Metrics endpoint for Prometheus scraping."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


async def metrics_middleware(request: Request, call_next: Callable):
    """Middleware to track request metrics."""
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Record metrics
    requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    return response


def track_agent_task(agent_role: str, status: str):
    """Track agent task completion."""
    agent_tasks_total.labels(agent_role=agent_role, status=status).inc()


def update_business_metrics(total_businesses: int, total_revenue: float):
    """Update business metrics."""
    active_businesses.set(total_businesses)
    revenue_total.set(total_revenue)


def track_ai_request(service: str, duration: float, status: str):
    """Track AI API request."""
    ai_requests.labels(service=service, status=status).inc()
    ai_request_duration.labels(service=service).observe(duration)


def track_payment(status: str):
    """Track payment transaction."""
    payment_transactions.labels(status=status).inc()


def track_subscription_change(plan: str, action: str):
    """Track subscription change."""
    subscription_changes.labels(plan=plan, action=action).inc()


def track_email_campaign(status: str):
    """Track email campaign."""
    email_campaigns.labels(status=status).inc()


def track_social_post(platform: str, status: str):
    """Track social media post."""
    social_posts.labels(platform=platform, status=status).inc()


def track_cache_access(cache_type: str, hit: bool):
    """Track cache access."""
    if hit:
        cache_hits.labels(cache_type=cache_type).inc()
    else:
        cache_misses.labels(cache_type=cache_type).inc()
