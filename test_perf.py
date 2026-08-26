import asyncio
from blank_business_builder.autonomous_business import AutonomousBusinessOrchestrator, AutonomousTask, AgentRole, TaskStatus

async def main():
    orchestrator = AutonomousBusinessOrchestrator("test", "founder")

    # Add 10,000 tasks
    for i in range(10000):
        task = AutonomousTask(
            task_id=f"task_{i}",
            role=AgentRole.RESEARCHER,
            description=f"Task {i}",
            status=TaskStatus.COMPLETED
        )
        orchestrator.task_queue.append(task)

    print(f"Task queue length: {len(orchestrator.task_queue)}")

    # Add one in-progress task
    task = AutonomousTask(
        task_id="in_progress_task",
        role=AgentRole.RESEARCHER,
        description="In progress task",
        status=TaskStatus.IN_PROGRESS
    )
    orchestrator.task_queue.append(task)
    orchestrator.task_status_counts[TaskStatus.IN_PROGRESS] = 1

    import time
    start = time.time()
    for _ in range(100):
        orchestrator._reconcile_orphaned_in_progress_tasks()
        in_progress = [t for t in orchestrator.task_queue if t.status == TaskStatus.IN_PROGRESS]
    end = time.time()

    print(f"Time for 100 reconciliations: {end - start:.4f}s")

if __name__ == "__main__":
    asyncio.run(main())
