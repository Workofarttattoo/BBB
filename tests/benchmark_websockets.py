import asyncio
import time
import sys
import os
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

# Add src to path if needed
sys.path.append(os.path.join(os.getcwd(), 'src'))

from blank_business_builder.websockets import get_business_metrics
from blank_business_builder.database import Business, AgentTask, MetricsHistory

# Mock classes to make the function work without a real DB but with delays
class MockQuery:
    def __init__(self, delay=0.1, result=None):
        self.delay = delay
        self.result = result

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def first(self):
        time.sleep(self.delay)  # Blocking sleep
        return self.result

    def all(self):
        time.sleep(self.delay)  # Blocking sleep
        return [self.result] if self.result else []

    def count(self):
        time.sleep(self.delay)  # Blocking sleep
        return 1

def create_mock_session():
    session = MagicMock(spec=Session)

    # Setup mock returns
    mock_business = MagicMock(spec=Business)
    mock_business.id = "test-id"
    mock_business.business_name = "Test Business"
    mock_business.total_revenue = 1000.0
    mock_business.status = "active"
    mock_business.business_concept = "Concept"
    mock_business.total_customers = 10
    mock_business.total_leads = 50
    mock_business.conversion_rate = 0.05

    mock_task = MagicMock(spec=AgentTask)
    mock_task.id = "task-id"
    mock_task.created_at = MagicMock()
    mock_task.created_at.isoformat.return_value = "2023-01-01T00:00:00"
    mock_task.completed_at = MagicMock()
    mock_task.completed_at.isoformat.return_value = "2023-01-01T01:00:00"
    mock_task.started_at = MagicMock()
    mock_task.started_at.isoformat.return_value = "2023-01-01T00:30:00"
    mock_task.agent_role = "sales"
    mock_task.task_type = "outreach"
    mock_task.status = "completed"
    mock_task.confidence = 0.95

    mock_metrics = MagicMock(spec=MetricsHistory)

    def side_effect(model):
        if model == Business:
            return MockQuery(delay=0.1, result=mock_business)
        elif model == AgentTask:
            return MockQuery(delay=0.1, result=mock_task)
        elif model == MetricsHistory:
            return MockQuery(delay=0.1, result=mock_metrics)
        return MockQuery()

    session.query.side_effect = side_effect
    return session

async def heartbeat(interval=0.01):
    """Monitor event loop latency."""
    max_delay = 0
    start_time = time.time()
    last_tick = start_time

    try:
        while True:
            await asyncio.sleep(interval)
            now = time.time()
            # If we slept for 'interval', elapsed should be 'interval'.
            # Any extra time is loop delay.
            actual_sleep = now - last_tick
            delay = actual_sleep - interval
            if delay > max_delay:
                max_delay = delay
            last_tick = now
    except asyncio.CancelledError:
        # Check one last time in case we were blocked during the last sleep
        now = time.time()
        actual_sleep = now - last_tick
        delay = actual_sleep - interval
        if delay > max_delay:
            max_delay = delay

    return max_delay

async def main():
    print("Starting benchmark...")

    # Setup mock session with artificial delays
    session = create_mock_session()

    # Start heartbeat monitor
    monitor_task = asyncio.create_task(heartbeat())

    # Allow heartbeat to start
    await asyncio.sleep(0.05)

    start_time = time.time()

    # Run the function under test
    print("Calling get_business_metrics...")
    try:
        result = await get_business_metrics("test-id", session)
    except Exception as e:
        print(f"Error calling get_business_metrics: {e}")
        monitor_task.cancel()
        return

    end_time = time.time()
    total_time = end_time - start_time

    # Stop monitor
    monitor_task.cancel()
    try:
        max_loop_delay = await monitor_task
    except asyncio.CancelledError:
        max_loop_delay = 0 # Should not happen if logic is right

    print(f"\nResults:")
    print(f"Total execution time: {total_time:.4f}s")
    print(f"Max event loop delay: {max_loop_delay:.4f}s")

    # Analysis
    if max_loop_delay > 0.05:
        print("\nConclusion: BLOCKED event loop! ❌")
        # Ensure we return non-zero exit code if blocked,
        # but for this "reproduce" step we just want to see the output.
    else:
        print("\nConclusion: Did NOT block event loop! ✅")

if __name__ == "__main__":
    asyncio.run(main())
