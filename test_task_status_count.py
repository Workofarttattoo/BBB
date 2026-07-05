import asyncio
from src.blank_business_builder.autonomous_business import AutonomousBusinessOrchestrator, AutonomousTask, AgentRole, TaskStatus

async def main():
    orchestrator = AutonomousBusinessOrchestrator(business_concept="Test Business", founder_name="Test")

    # Add tasks
    for i in range(100):
        orchestrator.add_task(AutonomousTask(task_id=f"t{i}", role=AgentRole.MARKETER, description="Test"))

    print(f"Task status counts: {orchestrator.task_status_counts}")

    in_progress = [t for t in orchestrator.task_queue if t.status == TaskStatus.IN_PROGRESS]
    print(f"In progress: {len(in_progress)}")

if __name__ == "__main__":
    asyncio.run(main())
