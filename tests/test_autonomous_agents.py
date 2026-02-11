import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add src to python path
sys.path.append(os.path.join(os.getcwd(), "src"))

from blank_business_builder.autonomous_business import AutonomousBusinessOrchestrator, AgentRole, TaskStatus, AutonomousTask

async def run_verification():
    orchestrator = AutonomousBusinessOrchestrator(
        business_concept="Test Business",
        founder_name="Tester",
        market_research_api_key="test",
        sendgrid_api_key="test",
        stripe_api_key="test",
        twitter_consumer_key="test",
        twitter_consumer_secret="test",
        twitter_access_token="test",
        twitter_access_token_secret="test"
    )

    await orchestrator.deploy_agents()

    # Verify new agents exist
    assert any(a.role == AgentRole.HR for a in orchestrator.agents.values()), "HR Agent not found"
    assert any(a.role == AgentRole.META_MANAGER for a in orchestrator.agents.values()), "Meta Manager not found"
    assert any(a.role == AgentRole.EXECUTIVE for a in orchestrator.agents.values()), "Executive Agent not found"
    assert any(a.role == AgentRole.DEEP_RESEARCHER for a in orchestrator.agents.values()), "Deep Research Agent not found"
    assert any(a.role == AgentRole.OSINT_SPECIALIST for a in orchestrator.agents.values()), "OSINT Specialist not found"
    assert any(a.role == AgentRole.CREATIVE_DIRECTOR for a in orchestrator.agents.values()), "Creative Director not found"

    # Verify HiveMind Registration
    assert len(orchestrator.hive_mind.agents) > 0, "No agents registered with HiveMind"

    # Test Scaling
    initial_count = len(orchestrator.agents)
    await orchestrator.scale_up_agents(AgentRole.SALES, count=5)
    assert len(orchestrator.agents) == initial_count + 5, "Scaling failed"

    # Force CEO improvement
    orchestrator.ceo.last_improvement_time = datetime.now() - timedelta(hours=2)

    # Run cycle
    await orchestrator.ceo.run_daemon_cycle()

    # Check if prompt registry updated (version > 1)
    updated = False
    for prompt in orchestrator.prompt_registry.get_all_prompts().values():
        if prompt.version > 1:
            updated = True
            break

    assert updated, "CEO did not update any prompt"

    # Verify HR Agent Logic
    hr_agent = next(a for a in orchestrator.agents.values() if a.role == AgentRole.HR)
    task = AutonomousTask(task_id="hr_test", role=AgentRole.HR, description="Test HR")
    plan = await hr_agent._plan_hr(task)

    assert plan['action'] == "hr_resource_management"

    # Verify Sales Logic includes Shift and Context
    sales_agent = next(a for a in orchestrator.agents.values() if a.role == AgentRole.SALES)
    task_sales = AutonomousTask(task_id="sales_test", role=AgentRole.SALES, description="Test Sales")
    plan_sales = await sales_agent._plan_sales(task_sales)

    assert "Shift" in str(plan_sales['steps']), "Sales plan missing shift context"
    assert "Ask for the sale" in str(plan_sales['steps']), "Sales plan missing 'Ask for sale' tactic"
    assert "COMMUNICATION PROTOCOLS" in plan_sales['context'], "Communication guidelines not injected"

def test_autonomous_agents_integration():
    """Run async verification in sync wrapper."""
    asyncio.run(run_verification())
