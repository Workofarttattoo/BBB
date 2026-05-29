"""
Proactive event-loop hooks — schedule / event / threshold triggers for Viktor agents.

Wire into Celery beat or a cron daemon. Agents wake themselves; humans are not required.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Awaitable, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

TaskHandler = Callable[[str], Awaitable[str]]


@dataclass
class ScheduledJob:
    job_id: str
    cron: str
    prompt: str
    agent_id: str = "echo"
    hour: int = 6
    minute: int = 0


@dataclass
class ThresholdJob:
    job_id: str
    metric_name: str
    threshold: float
    above: bool
    prompt: str


DEFAULT_JOBS: List[ScheduledJob] = [
    ScheduledJob(
        job_id="arxiv-ingest",
        cron="0 6 * * *",
        hour=6,
        minute=0,
        prompt=(
            "Ingest new arXiv papers (context provided), run invention extraction, "
            "append patent queue summary, post exec-ready brief."
        ),
    ),
    ScheduledJob(
        job_id="daily-ops",
        cron="0 7 * * *",
        hour=7,
        minute=0,
        prompt=(
            "Review overnight task queue, failed Celery jobs, judge revise loops, "
            "and Slack ops channel; post executive summary with action items."
        ),
    ),
]


class ProactiveScheduler:
    """Registry of proactive jobs — execution delegated to EchoViktorRunner or Celery."""

    def __init__(self, handler: Optional[TaskHandler] = None):
        self.handler = handler
        self.scheduled: List[ScheduledJob] = list(DEFAULT_JOBS)
        self.thresholds: List[ThresholdJob] = []

    def register_scheduled(self, job: ScheduledJob) -> None:
        self.scheduled.append(job)

    def register_threshold(self, job: ThresholdJob) -> None:
        self.thresholds.append(job)

    def get_job(self, job_id: str) -> Optional[ScheduledJob]:
        return next((j for j in self.scheduled if j.job_id == job_id), None)

    async def run_job(self, job_id: str) -> Optional[str]:
        job = self.get_job(job_id)
        if not job or not self.handler:
            logger.warning("No job or handler for %s", job_id)
            return None
        logger.info("Proactive scheduled run: %s", job_id)
        prompt = job.prompt
        if job_id == "arxiv-ingest":
            from .arxiv_ingest import fetch_recent_papers, format_papers_for_prompt

            papers = fetch_recent_papers()
            prompt = f"{job.prompt}\n\n{format_papers_for_prompt(papers)}"
        return await self.handler(prompt)

    async def check_thresholds(self, metrics: Dict[str, float]) -> List[str]:
        if not self.handler:
            return []
        results: List[str] = []
        for job in self.thresholds:
            value = metrics.get(job.metric_name)
            if value is None:
                continue
            fired = value > job.threshold if job.above else value < job.threshold
            if fired:
                logger.info("Threshold fired: %s (%s=%s)", job.job_id, job.metric_name, value)
                out = await self.handler(job.prompt)
                if out:
                    results.append(out)
        return results

    def celery_beat_schedule(self) -> Dict[str, Dict]:
        """Celery beat entries — import in tasks.py after crontab is available."""
        from celery.schedules import crontab

        entries: Dict[str, Dict] = {}
        for job in self.scheduled:
            schedule = crontab(
                hour=job.hour,
                minute=job.minute,
            )
            entries[f"viktor-{job.job_id}"] = {
                "task": "blank_business_builder.tasks.viktor_proactive_job",
                "schedule": schedule,
                "kwargs": {
                    "job_id": job.job_id,
                    "business_name": "SaaS Micro-Tools Empire",
                    "workspace": "saas-micro-tools",
                },
            }
        return entries

