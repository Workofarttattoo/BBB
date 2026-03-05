
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

async def monitor_event_loop(duration=2.5):
    """Monitor how much the event loop is blocked."""
    blocking_times = []
    start_monitoring = time.perf_counter()
    while time.perf_counter() - start_monitoring < duration:
        loop_start = time.perf_counter()
        await asyncio.sleep(0.1)
        loop_end = time.perf_counter()
        delay = loop_end - loop_start - 0.1
        if delay > 0.05:
            blocking_times.append(delay)
    return blocking_times

async def run_verification():
    print("Verifying performance improvement for asynchronous BufferService.get_profiles...")

    with patch("requests.get", side_effect=mock_get_with_delay):
        with patch.dict("os.environ", {"BUFFER_ACCESS_TOKEN": "test_token"}):
            service = BufferService()

            # Start monitoring event loop
            monitor_task = asyncio.create_task(monitor_event_loop())

            # Small delay to ensure monitor is running
            await asyncio.sleep(0.1)

            start_time = time.perf_counter()
            # Call asynchronous methods concurrently
            print("Calling get_profiles (async) x2 concurrently...")
            results = await asyncio.gather(
                service.get_profiles(),
                service.get_profiles()
            )
            end_time = time.perf_counter()

            total_time = end_time - start_time
            print(f"Total time for 2 concurrent calls: {total_time:.4f}s")

            blocking_times = await monitor_task
            if blocking_times:
                print(f"Event loop was blocked! Max blocking delay: {max(blocking_times):.4f}s")
                for i, bt in enumerate(blocking_times):
                    print(f"  Block {i+1}: {bt:.4f}s")
            else:
                print("✅ Success: Event loop was NOT significantly blocked.")

            if total_time < 1.5: # 2 concurrent 1s calls should finish in ~1s if truly async
                 print(f"✅ Performance boost confirmed! 2 calls finished in {total_time:.4f}s (vs >2s for sync)")
            else:
                 print(f"⚠️ Performance boost not fully realized. Total time: {total_time:.4f}s")

if __name__ == "__main__":
    asyncio.run(run_verification())
