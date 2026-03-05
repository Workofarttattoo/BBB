
import asyncio
import time
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Mock dependencies before importing integrations
sys.modules["openai"] = MagicMock()
sys.modules["anthropic"] = MagicMock()
sys.modules["sendgrid"] = MagicMock()
sys.modules["sendgrid.helpers.mail"] = MagicMock()
sys.modules["twilio"] = MagicMock()
sys.modules["twilio.rest"] = MagicMock()
sys.modules["tweepy"] = MagicMock()
sys.modules["requests"] = MagicMock()
sys.modules["fastapi"] = MagicMock()
sys.modules["fastapi.status"] = MagicMock()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from blank_business_builder.integrations import BufferService

def mock_get_with_delay(*args, **kwargs):
    time.sleep(1)  # Simulate 1 second network latency
    mock_response = MagicMock()
    mock_response.json.return_value = [{"id": "p1"}]
    mock_response.raise_for_status = MagicMock()
    return mock_response

async def monitor_event_loop():
    """Monitor how much the event loop is blocked."""
    blocking_times = []
    # Check for blocking every 0.1s for 2 seconds
    for _ in range(20):
        start = time.perf_counter()
        await asyncio.sleep(0.1)
        end = time.perf_counter()
        delay = end - start - 0.1
        if delay > 0.05:
            blocking_times.append(delay)
    return blocking_times

async def run_baseline():
    print("Establishing baseline for synchronous BufferService.get_profiles...")

    with patch("requests.get", side_effect=mock_get_with_delay):
        with patch.dict("os.environ", {"BUFFER_ACCESS_TOKEN": "test_token"}):
            service = BufferService()

            # Start monitoring event loop
            monitor_task = asyncio.create_task(monitor_event_loop())

            # Small delay to ensure monitor is running
            await asyncio.sleep(0.1)

            start_time = time.perf_counter()
            # Call synchronous method
            print("Calling get_profiles (sync)...")
            # In a real async app, calling a sync method like this blocks the whole loop
            profiles = service.get_profiles()
            end_time = time.perf_counter()

            total_time = end_time - start_time
            print(f"Total time for 1 call: {total_time:.4f}s")

            blocking_times = await monitor_task
            if blocking_times:
                print(f"Event loop was blocked! Max blocking delay: {max(blocking_times):.4f}s")
                for i, bt in enumerate(blocking_times):
                    print(f"  Block {i+1}: {bt:.4f}s")
            else:
                print("Event loop was not significantly blocked.")

if __name__ == "__main__":
    asyncio.run(run_baseline())
