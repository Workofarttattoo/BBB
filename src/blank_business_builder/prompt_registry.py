"""
Prompt Registry for Autonomous Agents
=====================================

Centralized store for all agent prompts, allowing for dynamic optimization
by the Chief Enhancement Officer.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from typing import Dict, Any, Optional
import logging
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class Prompt:
    """Represents a mutable prompt or instruction set."""
    key: str
    content: str
    description: str
    version: int = 1
    last_updated: datetime = field(default_factory=datetime.now)
    performance_score: float = 0.0  # Tracks effectiveness (0.0 - 1.0)
    history: list[str] = field(default_factory=list)

class PromptRegistry:
    """
    Manages all agent prompts and allows for runtime optimization.
    """
    def __init__(self):
        self._prompts: Dict[str, Prompt] = {}
        self._initialize_defaults()

    def _initialize_defaults(self):
        """Set initial default prompts for all agent roles."""

        # Research Agent Prompts
        self.register_prompt(
            "research_strategy",
            "Analyze target market demographics, identify top 10 competitors, track pricing strategies, monitor industry trends, generate insights report.",
            "Core instructions for market research agent."
        )

        # Marketing Agent Prompts
        self.register_prompt(
            "marketing_content_strategy",
            "Generate blog post (SEO-optimized), create social media content (LinkedIn, Twitter, Facebook), design email campaign, run Google Ads campaign, track engagement metrics.",
            "Core instructions for marketing agent content creation."
        )

        # Sales Agent Prompts
        self.register_prompt(
            "sales_outreach_strategy",
            "Generate lead list (100 prospects), craft personalized cold emails, schedule sales calls, conduct discovery calls, send proposals and close deals.",
            "Core instructions for sales outreach."
        )

        # HR / Finance Prompts
        self.register_prompt(
            "hr_finance_strategy",
            "Monitor agent resource usage, allocate budget tokens, track API costs, approve high-value transactions, generate financial health report.",
            "Core instructions for HR and Finance management."
        )

        # Meta Manager Prompts
        self.register_prompt(
            "meta_management_strategy",
            "Review sub-agent performance reports, identify bottlenecks in task queues, reassign blocked tasks, aggregate weekly progress for executive review.",
            "Core instructions for Meta Managers."
        )

        # Executive (Meta-Meta) Prompts
        self.register_prompt(
            "executive_strategy",
            "Set strategic quarterly goals, review meta-manager reports, approve major pivot decisions, analyze overall business health metrics.",
            "Core instructions for Executive (Meta-Meta) Managers."
        )

    def register_prompt(self, key: str, content: str, description: str):
        """Register a new prompt or reset an existing one."""
        self._prompts[key] = Prompt(key=key, content=content, description=description)
        logger.debug(f"Registered prompt: {key}")

    def get_prompt(self, key: str) -> str:
        """Retrieve the current content of a prompt."""
        if key not in self._prompts:
            logger.warning(f"Prompt '{key}' not found, returning empty string.")
            return ""
        return self._prompts[key].content

    def update_prompt(self, key: str, new_content: str, score_improvement: float = 0.0):
        """
        Update a prompt with a new version (e.g., from CEO optimization).

        Args:
            key: The prompt identifier
            new_content: The optimized prompt text
            score_improvement: Estimated improvement in performance
        """
        if key not in self._prompts:
            logger.error(f"Cannot update non-existent prompt: {key}")
            return

        prompt = self._prompts[key]
        prompt.history.append(prompt.content)  # Archive old version
        prompt.content = new_content
        prompt.version += 1
        prompt.last_updated = datetime.now()
        prompt.performance_score += score_improvement

        logger.info(f"Updated prompt '{key}' to version {prompt.version}")

    def get_all_prompts(self) -> Dict[str, Prompt]:
        """Return all managed prompts."""
        return self._prompts
