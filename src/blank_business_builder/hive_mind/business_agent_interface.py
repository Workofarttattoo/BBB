"""
BBB business role agents for QuLab Hive Mind task execution.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from .agent_interface import Level6AgentInterface
from .crystalline_intent import IntentParser
from .hive_mind_core import Agent, AgentType, HiveMind, Task, TaskPriority
from .semantic_lattice import ConceptNode

LOG = logging.getLogger(__name__)

BBB_ROLE_CAPABILITIES: Dict[AgentType, List[str]] = {
    AgentType.SALES: ["outbound", "pipeline", "crm", "proposals", "closing"],
    AgentType.MARKETING: ["content", "seo", "campaigns", "social", "positioning"],
    AgentType.SUPPORT: ["tickets", "onboarding", "docs", "escalation"],
    AgentType.EXECUTIVE: ["strategy", "prioritization", "governance", "okr"],
    AgentType.PRODUCT: ["roadmap", "features", "specs", "user_research"],
    AgentType.ACQUISITION: ["leads", "partnerships", "channels", "growth"],
    AgentType.ANALYTICS: ["metrics", "dashboards", "experiments", "forecasting"],
}

ROLE_TO_BBB: Dict[AgentType, str] = {
    AgentType.SALES: "sales",
    AgentType.MARKETING: "marketing",
    AgentType.SUPPORT: "support",
    AgentType.EXECUTIVE: "executive",
    AgentType.PRODUCT: "product",
    AgentType.ACQUISITION: "acquisition",
    AgentType.ANALYTICS: "analytics",
}


class BusinessRoleAgent(Level6AgentInterface):
    """Level-6 agent that delegates tasks to BBB RoleAgentRunner."""

    def __init__(
        self,
        agent: Agent,
        hive_mind: Optional[HiveMind] = None,
        *,
        business_name: str = "SaaS Micro-Tools Empire",
        workspace: str = "saas-micro-tools",
    ):
        super().__init__(agent, hive_mind)
        self.business_name = business_name
        self.workspace = workspace
        self.intent_parser = IntentParser()

    async def execute_task(self, task: Task) -> Dict[str, Any]:
        LOG.info("[info] BusinessRoleAgent %s executing: %s", self.agent.agent_id, task.description)
        role = ROLE_TO_BBB.get(self.agent.agent_type, "executive")
        prompt = task.description
        if task.parameters:
            prompt = f"{task.description}\n\nContext:\n{json.dumps(task.parameters, indent=2)}"

        try:
            from ..agent_ops_state import is_viktor_mode_enabled
            from ..ech0_viktor_runner import EchoViktorRunner
            from ..role_agent_runner import RoleAgentRunner

            if is_viktor_mode_enabled():
                runner = EchoViktorRunner(workspace=self.workspace, business_name=self.business_name)
                text = await runner.handle(
                    prompt,
                    agent_id=self.agent.agent_id,
                    task_id=task.task_id,
                )
                result = {"status": "success", "role": role, "summary": text, "mode": "viktor"}
            else:
                runner = RoleAgentRunner(self.business_name)
                artifact = await runner.run_task(
                    role=role,
                    task_id=task.task_id,
                    description=prompt,
                    agent_id=self.agent.agent_id,
                )
                result = {
                    "status": "success",
                    "role": role,
                    "summary": artifact.get("summary") or artifact.get("content") or str(artifact),
                    "artifact": {k: v for k, v in artifact.items() if k != "content"},
                    "mode": "role_runner",
                }
        except Exception as exc:
            LOG.exception("BusinessRoleAgent task failed")
            result = {"status": "error", "role": role, "error": str(exc)}

        self.learn_from_result(task, result)
        return result

    def learn_from_result(self, task: Task, result: Dict[str, Any]) -> None:
        confidence = 0.85 if result.get("status") == "success" else 0.4
        self.state.performance_history.append(confidence)
        concept = ConceptNode(
            node_id=f"bbb_task_{task.task_id}",
            concept_type="business_result",
            name=task.task_type,
            properties={"description": task.description, **result},
            confidence=confidence,
        )
        self.record_knowledge(concept)
        if self.hive_mind:
            self.hive_mind.knowledge.publish(
                "business_discoveries",
                {"task_id": task.task_id, "agent_id": self.agent.agent_id, "result": result},
                self.agent.agent_id,
            )


def create_business_agent(
    agent_type: AgentType,
    agent_id: str,
    hive_mind: Optional[HiveMind] = None,
    *,
    business_name: str = "SaaS Micro-Tools Empire",
    workspace: str = "saas-micro-tools",
) -> BusinessRoleAgent:
    caps = BBB_ROLE_CAPABILITIES.get(agent_type, ["general"])
    base = Agent(agent_id=agent_id, agent_type=agent_type, capabilities=caps)
    return BusinessRoleAgent(
        base,
        hive_mind,
        business_name=business_name,
        workspace=workspace,
    )


def create_bbb_agents(
    hive_mind: HiveMind,
    *,
    business_name: str = "SaaS Micro-Tools Empire",
    workspace: str = "saas-micro-tools",
    include_lab_agents: bool = False,
) -> List[Agent]:
    """Register BBB business agents (+ optional QuLab lab agents) on a HiveMind instance."""
    from .hive_mind_core import create_standard_agents

    agents: List[Agent] = []
    definitions = [
        (AgentType.EXECUTIVE, "bbb-executive-001"),
        (AgentType.SALES, "bbb-sales-001"),
        (AgentType.MARKETING, "bbb-marketing-001"),
        (AgentType.PRODUCT, "bbb-product-001"),
        (AgentType.ACQUISITION, "bbb-acquisition-001"),
        (AgentType.ANALYTICS, "bbb-analytics-001"),
        (AgentType.SUPPORT, "bbb-support-001"),
    ]
    for agent_type, agent_id in definitions:
        iface = create_business_agent(
            agent_type,
            agent_id,
            hive_mind,
            business_name=business_name,
            workspace=workspace,
        )
        hive_mind.register_agent(iface.agent, iface)
        agents.append(iface.agent)

    if include_lab_agents:
        agents.extend(create_standard_agents(hive_mind, auto_register=True))

    return agents
