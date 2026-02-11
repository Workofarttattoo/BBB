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

def test_autonomous_agents_integration():
    """Run async verification in sync wrapper."""
    asyncio.run(run_verification())
