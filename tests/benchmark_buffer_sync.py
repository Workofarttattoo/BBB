
import asyncio
import time
import sys
from unittest.mock import MagicMock, AsyncMock

# Mocking missing dependencies for the sake of the benchmark
class MockResponse:
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
    def json(self):
        return self.json_data
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP Error {self.status_code}")

def sync_get_simulated(url, params=None):
    # Simulate network latency
    time.sleep(0.1)
    return MockResponse([{"id": "p1"}])

async def async_get_simulated(url, params=None):
    # Simulate network latency
    await asyncio.sleep(0.1)
    return MockResponse([{"id": "p1"}])

async def run_sync_benchmark(n=10):
    print(f"Running synchronous benchmark with {n} requests...")
    start_time = time.perf_counter()

    # In a real app, these might be called from different tasks
    # but if they are sync, they block the loop one by one.
    for i in range(n):
        sync_get_simulated("http://api.bufferapp.com/1/profiles.json")

    end_time = time.perf_counter()
    duration = end_time - start_time
    print(f"Sync duration: {duration:.4f}s")
    return duration

async def run_async_benchmark(n=10):
    print(f"Running asynchronous benchmark with {n} requests...")
    start_time = time.perf_counter()

    tasks = []
    for i in range(n):
        tasks.append(async_get_simulated("http://api.bufferapp.com/1/profiles.json"))

    await asyncio.gather(*tasks)

    end_time = time.perf_counter()
    duration = end_time - start_time
    print(f"Async duration: {duration:.4f}s")
    return duration

async def main():
    n = 10
    sync_dur = await run_sync_benchmark(n)
    async_dur = await run_async_benchmark(n)

    improvement = (sync_dur - async_dur) / sync_dur * 100
    print(f"\nImprovement: {improvement:.2f}%")
    print(f"Async is {sync_dur / async_dur:.2f}x faster for {n} concurrent requests")

if __name__ == "__main__":
    asyncio.run(main())
