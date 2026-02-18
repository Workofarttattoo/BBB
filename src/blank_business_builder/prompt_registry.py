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

        # Deep Research Prompts
        self.register_prompt(
            "deep_research_strategy",
            "Conduct in-depth academic and market research. Cross-reference multiple sources, verify data integrity, and synthesize complex findings into actionable intelligence.",
            "Core instructions for Deep Research Agent."
        )

        # OSINT Prompts
        self.register_prompt(
            "osint_strategy",
            "Perform Open Source Intelligence gathering on competitors. Monitor social media, public filings, and news outlets. Identify vulnerabilities and strategic moves.",
            "Core instructions for OSINT Specialist."
        )

        # Creative Director Prompts
        self.register_prompt(
            "creative_director_strategy",
            "Oversee all creative output: text-to-image, text-to-video, voiceovers, ad creation, social media management, and text-to-music generation. Ensure brand consistency and high aesthetic quality.",
            "Core instructions for Creative Design Meta Agent."
        )

        # Communication Guidelines (Fine-tuning Context)
        self.register_prompt(
            "communication_guidelines",
            """
            COMMUNICATION PROTOCOLS:
            - Tone: Professional, disarming, witty, friendly. Never pressure.
            - Languages & Customs:
              - English: Direct but polite. Use standard business etiquette.
              - Spanish: Warm, relational. Use appropriate slang (e.g., 'Compadre' in MX contexts if informal, but stick to 'Estimado' for business). Build rapport first.
              - Korean: High respect (Honorifics). Bowing culture implies verbal deference. Use proper titles (Sajang-nim).
              - Chinese: Guanxi (relationship) focus. Indirect communication. Face-saving is crucial.
              - Japanese: Keigo (honorifics). Indirectness. High politeness. 'Sumimasen' (excuse me) is versatile.
            - Listening: Active listening. Wait for pauses. Acknowledge pain points before rebutting.
            """,
            "Guidelines for multi-cultural communication and tone."
        )

        # Sales Tactics (Fine-tuning Context)
        self.register_prompt(
            "sales_tactics",
            """
            SALES PROTOCOLS:
            - Goal: Always ask for the sale at least once. "Most people just need to be asked."
            - Rebuttals: Counter pain points with empathy and logic. "I understand X, and that's why Y solves it by..."
            - Hooks: Open with a question or a surprising stat. "Did you know 80% of..."
            - Closing: "Based on what we discussed, does this sound like the solution you've been looking for?"
            - Etiquette: No pressure. If they say no, ask for a referral or permission to follow up later.
            """,
            "Core sales tactics and closing strategies."
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
