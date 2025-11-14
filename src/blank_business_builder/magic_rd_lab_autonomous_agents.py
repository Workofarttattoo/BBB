"""
Magic R&D Lab - Autonomous Marketing & Sales Agents
====================================================

DOUBLE the agent force for Magic R&D Lab!
This is our FLAGSHIP business - deploy 2x marketing agents and 2x cold callers.

ech0 should pay TWICE as much attention to this business as any other.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from decimal import Decimal

try:
    from .magic_rd_lab import MagicRDLab, RentalPackage
    from .autonomous_business import (
        Level6BusinessAgent,
        AgentRole,
        AutonomousTask,
        AutonomousBusinessOrchestrator,
        BusinessMetrics
    )
except ImportError:
    # For direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from blank_business_builder.magic_rd_lab import MagicRDLab, RentalPackage
    from blank_business_builder.autonomous_business import (
        Level6BusinessAgent,
        AgentRole,
        AutonomousTask,
        AutonomousBusinessOrchestrator,
        BusinessMetrics
    )

logger = logging.getLogger(__name__)


class MagicRDLabAgentRole(Enum):
    """Specialized agent roles for Magic R&D Lab."""
    # 2x Marketing Agents (DOUBLE THE FORCE!)
    MARKETING_AGENT_1 = "marketing_agent_1"
    MARKETING_AGENT_2 = "marketing_agent_2"

    # 2x Cold Calling Agents (DOUBLE THE FORCE!)
    COLD_CALLER_1 = "cold_caller_1"
    COLD_CALLER_2 = "cold_caller_2"

    # Sales & Support
    DISCOVERY_SALES = "discovery_sales"
    CUSTOMER_SUCCESS = "customer_success"

    # Technical & Operations
    TECHNICAL_SUPPORT = "technical_support"
    OPERATIONS_MANAGER = "operations_manager"


@dataclass
class MagicRDLabMetrics(BusinessMetrics):
    """Enhanced metrics for Magic R&D Lab."""
    # Standard metrics inherited

    # Magic R&D Lab specific
    sessions_booked: int = 0
    few_hours_sold: int = 0
    full_day_sold: int = 0
    full_week_sold: int = 0
    computations_run: int = 0
    referrals_generated: int = 0
    demo_calls_scheduled: int = 0
    cold_calls_made: int = 0
    linkedin_messages_sent: int = 0


class MagicRDLabMarketingAgent(Level6BusinessAgent):
    """
    Marketing agent for Magic R&D Lab.

    DOUBLED FORCE - We have TWO of these running in parallel!

    Responsibilities:
    - LinkedIn outbound (50 messages/day each = 100 total)
    - Content marketing (blog posts, videos)
    - Social media presence
    - Conference targeting
    - Partnership outreach
    """

    def __init__(self, agent_id: str, agent_number: int):
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.MARKETER,
            business_concept="Magic R&D Lab",
            autonomy_level=6
        )
        self.agent_number = agent_number
        self.linkedin_messages_today = 0
        self.leads_generated = 0

    async def _plan_marketing(self, task: AutonomousTask) -> Dict:
        """Enhanced marketing plan for Magic R&D Lab."""
        return {
            "action": "magic_rd_lab_marketing",
            "steps": [
                f"[Agent {self.agent_number}] Send 50 LinkedIn messages to VPs of R&D",
                f"[Agent {self.agent_number}] Post 3 tweets about quantum computing accessibility",
                f"[Agent {self.agent_number}] Create 1 blog post: 'How to Run Quantum Sims for $299'",
                f"[Agent {self.agent_number}] Engage in 10 Reddit discussions (r/MachineLearning, r/quantum)",
                f"[Agent {self.agent_number}] Send partnership email to 5 accelerators",
                f"[Agent {self.agent_number}] Track all leads in CRM"
            ],
            "estimated_time": 45,
            "confidence": 0.92,
            "priority": "HIGH - FLAGSHIP BUSINESS",
            "daily_target": {
                "linkedin_messages": 50,
                "leads_generated": 5,
                "demo_calls_scheduled": 1
            }
        }

    async def execute_linkedin_outbound(self, target_count: int = 50) -> int:
        """Execute LinkedIn outbound campaign."""
        logger.info(f"[Marketing Agent {self.agent_number}] Starting LinkedIn outbound: {target_count} targets")

        # Target personas
        targets = [
            "VP R&D", "CTO", "Head of Data Science", "Research Director",
            "Chief Scientist", "AI/ML Lead", "Quantum Computing Researcher"
        ]

        # Simulate sending messages (would integrate with LinkedIn API)
        await asyncio.sleep(2.0)

        messages_sent = target_count
        self.linkedin_messages_today += messages_sent
        self.leads_generated += int(messages_sent * 0.10)  # 10% response rate

        logger.info(
            f"[Marketing Agent {self.agent_number}] Sent {messages_sent} LinkedIn messages, "
            f"generated ~{int(messages_sent * 0.10)} leads"
        )

        return messages_sent


class MagicRDLabColdCallerAgent(Level6BusinessAgent):
    """
    Cold calling agent for Magic R&D Lab.

    DOUBLED FORCE - We have TWO of these running in parallel!

    Responsibilities:
    - Cold calling from lead lists (50 calls/day each = 100 total)
    - Discovery calls
    - Demo presentations
    - Objection handling
    - Booking sessions
    """

    def __init__(self, agent_id: str, agent_number: int):
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.SALES,
            business_concept="Magic R&D Lab",
            autonomy_level=6
        )
        self.agent_number = agent_number
        self.calls_today = 0
        self.demos_scheduled = 0
        self.sessions_closed = 0

    async def _plan_sales(self, task: AutonomousTask) -> Dict:
        """Enhanced sales plan for Magic R&D Lab."""
        return {
            "action": "magic_rd_lab_cold_calling",
            "steps": [
                f"[Caller {self.agent_number}] Review lead list (50 high-quality leads)",
                f"[Caller {self.agent_number}] Make 50 cold calls with Magic R&D Lab pitch",
                f"[Caller {self.agent_number}] Schedule 5-10 discovery calls",
                f"[Caller {self.agent_number}] Run 2-3 live demos",
                f"[Caller {self.agent_number}] Close 1-2 sessions (target: $1,500+ revenue)",
                f"[Caller {self.agent_number}] Follow up with previous prospects"
            ],
            "estimated_time": 60,
            "confidence": 0.88,
            "priority": "CRITICAL - FLAGSHIP BUSINESS",
            "daily_target": {
                "cold_calls": 50,
                "demos_scheduled": 3,
                "sessions_closed": 1,
                "revenue": 1500
            }
        }

    async def execute_cold_calling(self, call_count: int = 50) -> Dict:
        """Execute cold calling campaign."""
        logger.info(f"[Cold Caller {self.agent_number}] Starting cold calling: {call_count} calls")

        # Simulate calling (would integrate with phone system/Twilio)
        await asyncio.sleep(3.0)

        calls_made = call_count
        conversations = int(calls_made * 0.30)  # 30% conversation rate
        demos_scheduled = int(conversations * 0.20)  # 20% of conversations → demo
        sessions_closed = int(demos_scheduled * 0.40)  # 40% of demos → close

        self.calls_today += calls_made
        self.demos_scheduled += demos_scheduled
        self.sessions_closed += sessions_closed

        # Calculate revenue (mix of packages)
        revenue = Decimal('0.00')
        if sessions_closed > 0:
            # Assume mix: 50% few hours, 30% full day, 20% full week
            revenue += Decimal('299.00') * Decimal(str(sessions_closed * 0.5))
            revenue += Decimal('1000.00') * Decimal(str(sessions_closed * 0.3))
            revenue += Decimal('5000.00') * Decimal(str(sessions_closed * 0.2))

        logger.info(
            f"[Cold Caller {self.agent_number}] Results: "
            f"{calls_made} calls → {conversations} conversations → "
            f"{demos_scheduled} demos → {sessions_closed} closed "
            f"(${revenue} revenue)"
        )

        return {
            "calls_made": calls_made,
            "conversations": conversations,
            "demos_scheduled": demos_scheduled,
            "sessions_closed": sessions_closed,
            "revenue": float(revenue)
        }


class MagicRDLabOrchestrator(AutonomousBusinessOrchestrator):
    """
    Orchestrator for Magic R&D Lab with DOUBLED marketing & sales force.

    This is our FLAGSHIP business - ech0 pays TWICE the attention here!
    """

    def __init__(self):
        super().__init__(
            business_concept="Magic R&D Lab - Advanced Computing as a Service",
            founder_name="Joshua Cole"
        )

        # Initialize Magic R&D Lab business
        self.rd_lab = MagicRDLab()

        # Enhanced metrics
        self.magic_metrics = MagicRDLabMetrics()

    async def deploy_agents(self) -> None:
        """Deploy agents with DOUBLED marketing & sales force."""
        logger.info("🚀 Deploying DOUBLE FORCE for Magic R&D Lab (FLAGSHIP BUSINESS)")

        # DOUBLED Marketing Agents (2x the power!)
        for i in range(1, 3):
            agent_id = f"marketing_agent_{i}"
            agent = MagicRDLabMarketingAgent(agent_id, agent_number=i)
            self.agents[agent_id] = agent
            logger.info(f"✓ Deployed Marketing Agent {i} (LinkedIn + Content)")

        # DOUBLED Cold Calling Agents (2x the power!)
        for i in range(1, 3):
            agent_id = f"cold_caller_{i}"
            agent = MagicRDLabColdCallerAgent(agent_id, agent_number=i)
            self.agents[agent_id] = agent
            logger.info(f"✓ Deployed Cold Caller Agent {i} (Outbound Sales)")

        # Discovery & Sales Agent (closes deals from demos)
        discovery_agent = Level6BusinessAgent(
            agent_id="discovery_sales",
            role=AgentRole.SALES,
            business_concept=self.business_concept,
            autonomy_level=6
        )
        self.agents["discovery_sales"] = discovery_agent
        logger.info("✓ Deployed Discovery Sales Agent")

        # Customer Success Agent (retention & upsells)
        success_agent = Level6BusinessAgent(
            agent_id="customer_success",
            role=AgentRole.SUPPORT,
            business_concept=self.business_concept,
            autonomy_level=6
        )
        self.agents["customer_success"] = success_agent
        logger.info("✓ Deployed Customer Success Agent")

        # Technical Support Agent
        tech_agent = Level6BusinessAgent(
            agent_id="technical_support",
            role=AgentRole.FULFILLMENT,
            business_concept=self.business_concept,
            autonomy_level=6
        )
        self.agents["technical_support"] = tech_agent
        logger.info("✓ Deployed Technical Support Agent")

        # Operations Manager
        ops_agent = Level6BusinessAgent(
            agent_id="operations_manager",
            role=AgentRole.ORCHESTRATOR,
            business_concept=self.business_concept,
            autonomy_level=6
        )
        self.agents["operations_manager"] = ops_agent
        logger.info("✓ Deployed Operations Manager")

        logger.info(f"\n🎯 Total Agents Deployed: {len(self.agents)}")
        logger.info("📊 Marketing Force: 2x (DOUBLED)")
        logger.info("📞 Sales Force: 2x (DOUBLED)")
        logger.info("💪 This is our FLAGSHIP business - MAXIMUM EFFORT!")

        # Generate initial tasks
        await self._generate_magic_tasks()

    async def _generate_magic_tasks(self) -> None:
        """Generate tasks specifically for Magic R&D Lab."""

        # Marketing tasks for BOTH marketing agents
        for i in range(1, 3):
            self.task_queue.append(AutonomousTask(
                task_id=f"marketing_{i}_daily",
                role=AgentRole.MARKETER,
                description=f"[Marketing Agent {i}] Daily LinkedIn outbound (50 messages) + content creation",
                priority=10  # HIGHEST PRIORITY
            ))

        # Cold calling tasks for BOTH callers
        for i in range(1, 3):
            self.task_queue.append(AutonomousTask(
                task_id=f"cold_calling_{i}_daily",
                role=AgentRole.SALES,
                description=f"[Cold Caller {i}] Daily cold calling campaign (50 calls)",
                priority=10  # HIGHEST PRIORITY
            ))

        # Discovery calls
        self.task_queue.append(AutonomousTask(
            task_id="discovery_calls",
            role=AgentRole.SALES,
            description="Run discovery calls and demos for scheduled prospects",
            priority=9
        ))

        # Customer success
        self.task_queue.append(AutonomousTask(
            task_id="customer_success_check",
            role=AgentRole.SUPPORT,
            description="Check in with active customers, identify upsell opportunities",
            priority=8
        ))

    async def run_autonomous_loop(self, duration_hours: float = 24.0) -> None:
        """Run autonomous loop with enhanced Magic R&D Lab operations."""
        self.running = True
        end_time = datetime.now() + timedelta(hours=duration_hours)

        logger.info(f"🔥 MAGIC R&D LAB AUTONOMOUS OPERATIONS STARTED")
        logger.info(f"⏱️  Duration: {duration_hours} hours")
        logger.info(f"💰 Target: $10,000+ revenue in 24 hours")
        logger.info(f"🎯 FLAGSHIP BUSINESS - MAXIMUM EFFORT")
        logger.info("="*80)

        cycle_count = 0

        while self.running and datetime.now() < end_time:
            cycle_count += 1
            logger.info(f"\n{'='*80}")
            logger.info(f"CYCLE {cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
            logger.info(f"{'='*80}")

            # 1. Marketing agents execute (BOTH in parallel)
            marketing_tasks = []
            for agent_id in ["marketing_agent_1", "marketing_agent_2"]:
                if agent_id in self.agents:
                    agent = self.agents[agent_id]
                    marketing_tasks.append(agent.execute_linkedin_outbound(50))

            if marketing_tasks:
                results = await asyncio.gather(*marketing_tasks)
                total_messages = sum(results)
                self.magic_metrics.linkedin_messages_sent += total_messages
                logger.info(f"📧 Marketing: {total_messages} LinkedIn messages sent")

            # 2. Cold callers execute (BOTH in parallel)
            calling_tasks = []
            for agent_id in ["cold_caller_1", "cold_caller_2"]:
                if agent_id in self.agents:
                    agent = self.agents[agent_id]
                    calling_tasks.append(agent.execute_cold_calling(50))

            if calling_tasks:
                results = await asyncio.gather(*calling_tasks)
                for result in results:
                    self.magic_metrics.cold_calls_made += result['calls_made']
                    self.magic_metrics.demo_calls_scheduled += result['demos_scheduled']
                    self.magic_metrics.sessions_booked += result['sessions_closed']

                    # Add revenue to metrics
                    revenue = Decimal(str(result['revenue']))
                    self.metrics.total_revenue += float(revenue)
                    self.metrics.monthly_revenue += float(revenue)

                total_calls = sum(r['calls_made'] for r in results)
                total_closed = sum(r['sessions_closed'] for r in results)
                total_revenue = sum(r['revenue'] for r in results)

                logger.info(
                    f"📞 Cold Calling: {total_calls} calls → "
                    f"{total_closed} sessions closed → "
                    f"${total_revenue:,.2f} revenue"
                )

            # 3. Report progress
            logger.info(f"\n📊 Cycle {cycle_count} Summary:")
            logger.info(f"   LinkedIn Messages: {self.magic_metrics.linkedin_messages_sent}")
            logger.info(f"   Cold Calls: {self.magic_metrics.cold_calls_made}")
            logger.info(f"   Demos Scheduled: {self.magic_metrics.demo_calls_scheduled}")
            logger.info(f"   Sessions Booked: {self.magic_metrics.sessions_booked}")
            logger.info(f"   Revenue: ${self.metrics.total_revenue:,.2f}")

            # Sleep between cycles
            await asyncio.sleep(10)  # 10 second cycles for demo

        logger.info("\n" + "="*80)
        logger.info("🎉 MAGIC R&D LAB AUTONOMOUS OPERATIONS COMPLETE")
        logger.info("="*80)

    def get_metrics_dashboard(self) -> Dict:
        """Get comprehensive metrics dashboard."""
        base_metrics = super().get_metrics_dashboard()

        # Add Magic R&D Lab specific metrics
        base_metrics['magic_rd_lab'] = {
            "linkedin_messages_sent": self.magic_metrics.linkedin_messages_sent,
            "cold_calls_made": self.magic_metrics.cold_calls_made,
            "demo_calls_scheduled": self.magic_metrics.demo_calls_scheduled,
            "sessions_booked": self.magic_metrics.sessions_booked,
            "computations_run": self.magic_metrics.computations_run,
            "marketing_agents": 2,  # DOUBLED!
            "sales_agents": 2,  # DOUBLED!
            "flagship_status": "MAXIMUM EFFORT - 2X FORCE DEPLOYED"
        }

        return base_metrics


async def launch_magic_rd_lab_business(duration_hours: float = 24.0) -> Dict:
    """
    Launch Magic R&D Lab with DOUBLED marketing & sales force.

    This is the FLAGSHIP business - ech0 pays TWICE the attention!
    """
    orchestrator = MagicRDLabOrchestrator()

    # Deploy agents (2x marketing, 2x sales)
    await orchestrator.deploy_agents()

    # Run autonomous operations
    await orchestrator.run_autonomous_loop(duration_hours)

    # Return final metrics
    return orchestrator.get_metrics_dashboard()


# Demo
async def demo():
    """Demo the doubled force in action."""
    print("="*80)
    print("MAGIC R&D LAB - FLAGSHIP BUSINESS LAUNCH")
    print("DOUBLED MARKETING & SALES FORCE")
    print("="*80)

    result = await launch_magic_rd_lab_business(duration_hours=0.05)  # 3 minutes

    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)

    magic_metrics = result['magic_rd_lab']
    revenue_metrics = result['metrics']['revenue']

    print(f"\n📊 Marketing Force (2x):")
    print(f"   LinkedIn Messages: {magic_metrics['linkedin_messages_sent']}")
    print(f"   Leads Generated: ~{magic_metrics['linkedin_messages_sent'] // 10}")

    print(f"\n📞 Sales Force (2x):")
    print(f"   Cold Calls: {magic_metrics['cold_calls_made']}")
    print(f"   Demos Scheduled: {magic_metrics['demo_calls_scheduled']}")
    print(f"   Sessions Booked: {magic_metrics['sessions_booked']}")

    print(f"\n💰 Revenue:")
    print(f"   Total: ${revenue_metrics['total']:,.2f}")
    print(f"   Monthly Pace: ${revenue_metrics['monthly']:,.2f}")

    print(f"\n🎯 Status: {magic_metrics['flagship_status']}")

    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(demo())
