"""Embedded Jiminy Cricket module for ethical checkpoints."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, Iterator, Optional
import logging

DEFAULT_REMINDERS = [
    "Operate only within approved jurisdictions and scenarios.",
    "Use official government portals when submitting sensitive forms.",
    "Record manual verification steps for any filings.",
]


@dataclass
class ConscienceConfig:
    """Configuration for the Jiminy Cricket conscience layer."""

    enabled: bool = True
    checks: list[Callable[[], bool]] = field(default_factory=list)
    reminders: list[str] = field(default_factory=lambda: list(DEFAULT_REMINDERS))
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("jiminy_cricket"))


class JiminyCricket:
    """Drop-in guardian for runtime behaviour and reminders."""

    def __init__(self, config: Optional[ConscienceConfig] = None) -> None:
        self.config = config or ConscienceConfig()
        if not self.config.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("[jiminy] %(levelname)s %(message)s")
            handler.setFormatter(formatter)
            self.config.logger.addHandler(handler)
        self.config.logger.setLevel(logging.INFO)

    def affirm(self, message: str) -> None:
        if self.config.enabled:
            self.config.logger.info(message)

    def run_checks(self) -> bool:
        if not self.config.enabled:
            return True
        failed: list[str] = []
        for check in self.config.checks:
            try:
                if not check():
                    failed.append(check.__name__)
            except Exception as exc:
                self.config.logger.error("Check %s crashed: %s", check.__name__, exc)
                failed.append(check.__name__)
        if failed:
            self.config.logger.warning("Checks failed: %s", ", ".join(failed))
            return False
        self.config.logger.info("All Jiminy checks passed.")
        return True

    def remind(self) -> None:
        if not self.config.enabled:
            return
        for note in self.config.reminders:
            self.config.logger.info("Reminder: %s", note)

    @contextmanager
    def conscience(self, task_name: str) -> Iterator[None]:
        start = datetime.utcnow()
        self.config.logger.info("Beginning %s with Jiminy oversight", task_name)
        try:
            yield
        finally:
            duration = (datetime.utcnow() - start).total_seconds()
            self.config.logger.info("Completed %s in %.2fs", task_name, duration)
            self.remind()


def create_jiminy(
    enabled: bool = True,
    checks: Optional[Iterable[Callable[[], bool]]] = None,
    reminders: Optional[Iterable[str]] = None,
) -> JiminyCricket:
    config = ConscienceConfig(
        enabled=enabled,
        checks=list(checks or []),
        reminders=list(reminders or []),
    )
    return JiminyCricket(config=config)


def check_license_file(path: Path = Path("LICENSE")) -> Callable[[], bool]:
    def _inner() -> bool:
        exists = path.exists()
        if not exists:
            logging.getLogger("jiminy_cricket").warning("License file missing at %s", path)
        return exists

    _inner.__name__ = f"check_license_file_{path.name}"
    return _inner
