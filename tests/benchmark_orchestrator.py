
import asyncio
import time
from src.blank_business_builder.autonomous_business import AutonomousBusinessOrchestrator, AutonomousTask, AgentRole, TaskStatus
import logging

# Disable logging for benchmark
logging.getLogger("src.blank_business_builder.autonomous_business").setLevel(logging.ERROR)

async def benchmark():
    print("Initializing Orchestrator...")
    orchestrator = AutonomousBusinessOrchestrator("Benchmark", "Bolt")

    # Add 10,000 tasks
    print("Adding 10,000 tasks...")
    for i in range(10000):
        task = AutonomousTask(
            task_id=f"t{i}",
            role=AgentRole.RESEARCHER,
            description=f"Task {i}",
            status=TaskStatus.PENDING
        )
        orchestrator.add_task(task)

        # Mark some as completed/failed using the internal method to keep counters in sync
        if i % 2 == 0:
            orchestrator._set_task_status(task, TaskStatus.COMPLETED)
        elif i % 3 == 0:
            orchestrator._set_task_status(task, TaskStatus.FAILED)

    # Measure get_metrics_dashboard time (should be O(1))
    start_time = time.time()
    dashboard = orchestrator.get_metrics_dashboard()
    end_time = time.time()

    duration = end_time - start_time
    print(f"get_metrics_dashboard took: {duration:.6f} seconds")

    # Verify counts roughly
    metrics = dashboard["metrics"]["operations"]
    print(f"Tasks Completed: {metrics['tasks_completed']}") # note: tasks_completed in metrics is cumulative count of completions, but tasks_by_status is current state
    print(f"Tasks Pending: {metrics['tasks_pending']}")
    print(f"Status Counts: {metrics['tasks_by_status']}")

    # Measure _report_progress time (simulated logic)
    # New logic: O(1) dictionary lookup
    start_time = time.time()
    pending_count = orchestrator.task_status_counts[TaskStatus.PENDING]
    end_time = time.time()
    print(f"Counting pending tasks took: {end_time - start_time:.6f} seconds")

    return duration

if __name__ == "__main__":
    asyncio.run(benchmark())
