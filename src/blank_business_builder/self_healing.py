"""
Self-Healing Orchestrator for Better Business Builder.

Keeps critical dependencies healthy by running probes and auto-recovery actions.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Dict, Optional

from .database import get_db_engine, init_db

logger = logging.getLogger(__name__)


HealthCheck = Callable[[], Awaitable[bool]]
RecoveryAction = Callable[[], Awaitable[None]]


@dataclass
class Probe:
    """Probe definition with optional recovery action."""
    name: str
    check: HealthCheck
    recover: Optional[RecoveryAction] = None


@dataclass
class SelfHealingConfig:
    """Config options for the self-healing loop."""
    interval_seconds: int = 30
    failure_threshold: int = 3
    cooldown_seconds: int = 120
    init_db_on_recover: bool = False


class DatabaseProbe:
    """Database connectivity probe with re-initialization recovery."""

    def __init__(self, database_url: Optional[str], init_db_on_recover: bool) -> None:
        self.database_url = database_url
        self.init_db_on_recover = init_db_on_recover
        self.engine = get_db_engine(database_url)

    async def check(self) -> bool:
        return await asyncio.to_thread(self._ping)

    def _ping(self) -> bool:
        try:
            with self.engine.connect() as connection:
                connection.execute("SELECT 1")
            return True
        except Exception as exc:
            logger.warning("Database probe failed: %s", exc)
            return False

    async def recover(self) -> None:
        await asyncio.to_thread(self._recover_sync)

    def _recover_sync(self) -> None:
        logger.info("Database recovery started.")
        self.engine.dispose()
        self.engine = get_db_engine(self.database_url)
        if self.init_db_on_recover:
            init_db(self.database_url)
        logger.info("Database recovery completed.")


class SelfHealingOrchestrator:
    """Run probes and recover components when they fail repeatedly."""

    def __init__(self, config: SelfHealingConfig) -> None:
        self.config = config
        self.probes: Dict[str, Probe] = {}
        self._failure_counts: Dict[str, int] = {}
        self._last_recovery: Dict[str, float] = {}
        self._stop_event = asyncio.Event()

    def register_probe(self, probe: Probe) -> None:
        self.probes[probe.name] = probe

    async def run(self) -> None:
        logger.info("Self-healing loop started.")
        while not self._stop_event.is_set():
            await self._tick()
            await asyncio.sleep(self.config.interval_seconds)

    async def stop(self) -> None:
        self._stop_event.set()

    async def _tick(self) -> None:
        for name, probe in self.probes.items():
            healthy = await probe.check()
            if healthy:
                self._failure_counts[name] = 0
                continue

            failures = self._failure_counts.get(name, 0) + 1
            self._failure_counts[name] = failures
            logger.warning("Probe %s failed (%s/%s).", name, failures, self.config.failure_threshold)

            if failures < self.config.failure_threshold or not probe.recover:
                continue

            last_recovery = self._last_recovery.get(name, 0.0)
            if time.time() - last_recovery < self.config.cooldown_seconds:
                continue

            logger.info("Triggering recovery for probe %s.", name)
            await probe.recover()
            self._last_recovery[name] = time.time()
            self._failure_counts[name] = 0


def build_self_healing_orchestrator() -> SelfHealingOrchestrator:
    """Create orchestrator with default probes."""
    config = SelfHealingConfig(
        interval_seconds=int(os.getenv("SELF_HEALING_INTERVAL_SECONDS", "30")),
        failure_threshold=int(os.getenv("SELF_HEALING_FAILURE_THRESHOLD", "3")),
        cooldown_seconds=int(os.getenv("SELF_HEALING_COOLDOWN_SECONDS", "120")),
        init_db_on_recover=os.getenv("SELF_HEALING_INIT_DB", "false").lower() == "true",
    )
    orchestrator = SelfHealingOrchestrator(config)

    database_url = os.getenv("DATABASE_URL")
    db_probe = DatabaseProbe(database_url, config.init_db_on_recover)
    orchestrator.register_probe(Probe(name="database", check=db_probe.check, recover=db_probe.recover))

    return orchestrator


def self_healing_enabled() -> bool:
    """Check if self-healing is enabled via environment variable."""
    return os.getenv("SELF_HEALING_ENABLED", "false").lower() == "true"
