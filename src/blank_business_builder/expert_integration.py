"""
Expert System Integration with BBB Autonomous Business
=======================================================

Integrates multi-domain expert system with BBB autonomous agents
to provide specialized domain knowledge and decision support.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from .expert_system import (
    MultiDomainExpertSystem,
    ExpertDomain,
    ExpertQuery,
    ExpertResponse,
    EnsembleResponse,
    KnowledgeDocument
)
from .expert_finetuning import (
    ExpertFineTuner,
    TrainingStrategy,
    TrainingDataset,
    TrainingExample,
    DatasetGenerator
)
from .autonomous_business import (
    Level6BusinessAgent,
    AgentRole,
    AutonomousTask,
    AutonomousBusinessOrchestrator
)

logger = logging.getLogger(__name__)


class ExpertEnhancedBusinessAgent(Level6BusinessAgent):
    """
    Level 6 Business Agent enhanced with domain expert consultation.

    Augments autonomous business operations with specialized domain knowledge
    from chemistry, biology, physics, materials science and other expert domains.
    """

    def __init__(
        self,
        agent_id: str,
        role: AgentRole,
        business_concept: str,
        autonomy_level: int = 6,
        expert_system: Optional[MultiDomainExpertSystem] = None
    ):
        super().__init__(agent_id, role, business_concept, autonomy_level)
        self.expert_system = expert_system
        self.expert_consultation_count = 0

    async def _decide(self, world_model: Dict, task: AutonomousTask) -> Dict:
        """Enhanced decision making with expert consultation."""
        # Get base decision from Level 6 agent
        base_decision = await super()._decide(world_model, task)

        # Consult experts if available and relevant
        if self.expert_system and self._should_consult_expert(task):
            expert_insight = await self._consult_experts(task, world_model)

            if expert_insight:
                # Augment decision with expert knowledge
                base_decision['expert_insight'] = expert_insight
                base_decision['confidence'] *= 1.1  # Boost confidence with expert backing
                base_decision['steps'].insert(0, f"Apply expert insight: {expert_insight['summary']}")

                self.expert_consultation_count += 1
                logger.info(f"[{self.agent_id}] Enhanced decision with expert consultation")

        return base_decision

    def _should_consult_expert(self, task: AutonomousTask) -> bool:
        """Determine if task would benefit from expert consultation."""
        # Consult experts for complex or specialized tasks
        keywords = ['research', 'analysis', 'technical', 'science', 'optimize', 'design', 'develop']
        return any(keyword in task.description.lower() for keyword in keywords)

    async def _consult_experts(self, task: AutonomousTask, world_model: Dict) -> Optional[Dict]:
        """Consult domain experts for task."""
        try:
            # Determine relevant domain
            domain = self._map_task_to_domain(task)

            if not domain:
                return None

            # Query expert system
            query = ExpertQuery(
                query=task.description,
                domain=domain,
                context=world_model,
                use_ensemble=True  # Use multiple experts for robustness
            )

            response = await self.expert_system.query(query)

            if isinstance(response, EnsembleResponse):
                return {
                    'summary': response.consensus_answer[:200],
                    'confidence': response.confidence,
                    'agreement': response.agreement_score,
                    'domains': [d.value for d in response.domains_consulted]
                }
            else:
                return {
                    'summary': response.answer[:200],
                    'confidence': response.confidence,
                    'domain': response.domain.value,
                    'sources': len(response.sources)
                }

        except Exception as e:
            logger.error(f"Expert consultation failed: {e}")
            return None

    def _map_task_to_domain(self, task: AutonomousTask) -> Optional[ExpertDomain]:
        """Map business task to expert domain."""
        description = task.description.lower()

        # Science & engineering domains
        if any(word in description for word in ['chemistry', 'chemical', 'molecule', 'compound']):
            return ExpertDomain.CHEMISTRY
        elif any(word in description for word in ['biology', 'biological', 'organism', 'cell', 'dna']):
            return ExpertDomain.BIOLOGY
        elif any(word in description for word in ['physics', 'physical', 'quantum', 'mechanics']):
            return ExpertDomain.PHYSICS
        elif any(word in description for word in ['material', 'crystalline', 'properties']):
            return ExpertDomain.MATERIALS_SCIENCE

        # Business domains
        elif any(word in description for word in ['marketing', 'advertising', 'campaign']):
            return ExpertDomain.MARKETING
        elif any(word in description for word in ['finance', 'financial', 'accounting', 'revenue']):
            return ExpertDomain.FINANCE
        elif any(word in description for word in ['sales', 'selling', 'customer']):
            return ExpertDomain.SALES

        # Data & AI domains
        elif any(word in description for word in ['data', 'analytics', 'statistics']):
            return ExpertDomain.DATA_SCIENCE
        elif any(word in description for word in ['machine learning', 'ai', 'neural', 'model']):
            return ExpertDomain.MACHINE_LEARNING

        return None


class ExpertEnhancedOrchestrator(AutonomousBusinessOrchestrator):
    """
    Orchestrator enhanced with expert system.

    Coordinates expert-enhanced agents and provides system-wide
    expert consultation capabilities.
    """

    def __init__(
        self,
        business_concept: str,
        founder_name: str,
        enable_experts: bool = True
    ):
        super().__init__(business_concept, founder_name)
        self.enable_experts = enable_experts
        self.expert_system: Optional[MultiDomainExpertSystem] = None
        self.expert_finetuner: Optional[ExpertFineTuner] = None

        if enable_experts:
            self._initialize_expert_system()

    def _initialize_expert_system(self) -> None:
        """Initialize expert system and fine-tuner."""
        try:
            from .expert_system import CHROMADB_AVAILABLE

            self.expert_system = MultiDomainExpertSystem(use_chromadb=CHROMADB_AVAILABLE)

            # Add initial knowledge base
            self._populate_knowledge_base()

            # Initialize fine-tuner
            self.expert_finetuner = ExpertFineTuner(
                self.expert_system,
                strategy=TrainingStrategy.SUPERVISED_LEARNING
            )

            # Fine-tune experts on relevant domains
            asyncio.create_task(self._fine_tune_experts())

            logger.info("✓ Expert system initialized")

        except Exception as e:
            logger.warning(f"Expert system initialization failed: {e}")
            self.enable_experts = False

    def _populate_knowledge_base(self) -> None:
        """Populate expert system with business-relevant knowledge."""
        # Add business domain knowledge
        business_docs = [
            KnowledgeDocument(
                doc_id="biz_001",
                content="Market research identifies customer needs, competitors, and market size. Essential for business strategy.",
                domain=ExpertDomain.MARKETING,
                metadata={"source": "business_fundamentals", "topic": "market_research"}
            ),
            KnowledgeDocument(
                doc_id="biz_002",
                content="Sales funnel stages: Awareness, Interest, Decision, Action. Optimize conversion at each stage.",
                domain=ExpertDomain.SALES,
                metadata={"source": "sales_fundamentals", "topic": "sales_funnel"}
            ),
            KnowledgeDocument(
                doc_id="biz_003",
                content="Revenue forecasting uses historical data, market trends, and growth assumptions to predict future income.",
                domain=ExpertDomain.FINANCE,
                metadata={"source": "finance_fundamentals", "topic": "forecasting"}
            ),
            KnowledgeDocument(
                doc_id="biz_004",
                content="Customer retention is 5-25x cheaper than acquisition. Focus on satisfaction and value delivery.",
                domain=ExpertDomain.OPERATIONS,
                metadata={"source": "operations_fundamentals", "topic": "retention"}
            )
        ]

        self.expert_system.add_knowledge(business_docs)

    async def _fine_tune_experts(self) -> None:
        """Fine-tune experts on business-relevant datasets."""
        try:
            # Generate or load training datasets
            datasets = {
                ExpertDomain.CHEMISTRY: DatasetGenerator.generate_chemistry_dataset(30),
                ExpertDomain.BIOLOGY: DatasetGenerator.generate_biology_dataset(30),
                ExpertDomain.PHYSICS: DatasetGenerator.generate_physics_dataset(30)
            }

            # Fine-tune each expert
            for domain, dataset in datasets.items():
                logger.info(f"Fine-tuning {domain.value} expert...")

                result = await self.expert_finetuner.fine_tune_expert(
                    domain=domain,
                    dataset=dataset,
                    epochs=3,
                    batch_size=10,
                    learning_rate=0.01
                )

                logger.info(
                    f"✓ {domain.value} expert fine-tuned - "
                    f"Improvement: {result.improvement:+.3f}"
                )

        except Exception as e:
            logger.error(f"Expert fine-tuning failed: {e}")

    async def deploy_agents(self) -> None:
        """Deploy expert-enhanced agents."""
        logger.info(f"Deploying expert-enhanced autonomous agents for: {self.business_concept}")

        # Create expert-enhanced agent for each role
        for role in AgentRole:
            agent_id = f"{role.value}_agent_{int(asyncio.get_event_loop().time())}"

            if self.enable_experts:
                agent = ExpertEnhancedBusinessAgent(
                    agent_id=agent_id,
                    role=role,
                    business_concept=self.business_concept,
                    autonomy_level=6,
                    expert_system=self.expert_system
                )
            else:
                agent = Level6BusinessAgent(
                    agent_id=agent_id,
                    role=role,
                    business_concept=self.business_concept,
                    autonomy_level=6
                )

            self.agents[agent_id] = agent
            logger.info(f"✓ Deployed {role.value} agent: {agent_id}")

        # Generate initial tasks
        await self._generate_initial_tasks()

    async def consult_expert_ensemble(self, query: str) -> Optional[EnsembleResponse]:
        """Consult expert ensemble for orchestrator-level decisions."""
        if not self.expert_system:
            return None

        try:
            expert_query = ExpertQuery(
                query=query,
                use_ensemble=True,
                confidence_threshold=0.6
            )

            response = await self.expert_system.query(expert_query)

            if isinstance(response, EnsembleResponse):
                return response

        except Exception as e:
            logger.error(f"Expert ensemble consultation failed: {e}")

        return None

    def get_expert_metrics(self) -> Dict[str, Any]:
        """Get expert system performance metrics."""
        if not self.expert_system:
            return {"enabled": False}

        status = self.expert_system.get_system_status()

        # Add agent-level expert usage
        agent_consultations = sum(
            agent.expert_consultation_count
            for agent in self.agents.values()
            if isinstance(agent, ExpertEnhancedBusinessAgent)
        )

        return {
            "enabled": True,
            "total_consultations": agent_consultations,
            "expert_system_status": status
        }


async def launch_expert_enhanced_business(
    business_concept: str,
    founder_name: str,
    duration_hours: float = 24.0,
    enable_experts: bool = True
) -> Dict:
    """
    Launch autonomous business with expert system enhancement.

    Args:
        business_concept: Type of business to run
        founder_name: Owner's name
        duration_hours: How long to run autonomously
        enable_experts: Whether to enable expert system

    Returns:
        Final business metrics including expert system stats
    """
    orchestrator = ExpertEnhancedOrchestrator(
        business_concept,
        founder_name,
        enable_experts=enable_experts
    )

    # Deploy expert-enhanced agents
    await orchestrator.deploy_agents()

    # Run autonomously
    await orchestrator.run_autonomous_loop(duration_hours)

    # Get final metrics
    metrics = orchestrator.get_metrics_dashboard()

    # Add expert metrics
    metrics['expert_system'] = orchestrator.get_expert_metrics()

    return metrics


# CLI interface
async def main():
    """CLI interface for expert-enhanced autonomous business."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m blank_business_builder.expert_integration <business_concept> [founder_name] [duration_hours]")
        print("\nExample:")
        print("  python -m blank_business_builder.expert_integration 'AI Consulting' 'Joshua Cole' 0.1")
        sys.exit(1)

    business_concept = sys.argv[1]
    founder_name = sys.argv[2] if len(sys.argv) > 2 else "Founder"
    duration_hours = float(sys.argv[3]) if len(sys.argv) > 3 else 0.1

    print("="*80)
    print("Expert-Enhanced Autonomous Business")
    print("="*80)
    print(f"Business: {business_concept}")
    print(f"Founder: {founder_name}")
    print(f"Duration: {duration_hours} hours")
    print("="*80)

    result = await launch_expert_enhanced_business(
        business_concept=business_concept,
        founder_name=founder_name,
        duration_hours=duration_hours,
        enable_experts=True
    )

    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)

    import json
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
