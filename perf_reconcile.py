import asyncio
from blank_business_builder.autonomous_business import AutonomousBusinessOrchestrator, AutonomousTask, AgentRole, TaskStatus

async def test():
    orchestrator = AutonomousBusinessOrchestrator("test_biz", "test_founder")

    # 1. Add 10,000 completed tasks to history
    for i in range(10000):
        task = AutonomousTask(
            task_id=f"t_{i}",
            role=AgentRole.RESEARCHER,
            description="done",
            status=TaskStatus.COMPLETED
        )
        orchestrator.task_queue.append(task)

    # 2. Add 5 in-progress tasks
    for i in range(5):
        task = AutonomousTask(
            task_id=f"ip_{i}",
            role=AgentRole.RESEARCHER,
            description="in prog",
            status=TaskStatus.IN_PROGRESS,
            assigned_to="agent_1"
        )
        orchestrator.task_queue.append(task)
        orchestrator.task_status_counts[TaskStatus.IN_PROGRESS] += 1

    import time
    start = time.time()
    for _ in range(100):
        # The bottleneck operations
        orchestrator._reconcile_orphaned_in_progress_tasks()
        _ = [t for t in orchestrator.task_queue if t.status == TaskStatus.IN_PROGRESS]

    elapsed = time.time() - start
    print(f"Original Time: {elapsed:.4f}s")

if __name__ == "__main__":
    asyncio.run(test())
