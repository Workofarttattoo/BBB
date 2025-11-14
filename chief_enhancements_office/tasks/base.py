"""Base task for Chief Enhancements meta-agent."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..meta_agent import EnhancementContext


class EnhancementTask(ABC):
    name = "enhancement-task"

    @abstractmethod
    def execute(self, ctx: "EnhancementContext", *, options: dict[str, Any]) -> None:
        """Perform improvement work."""


__all__ = ["EnhancementTask"]
