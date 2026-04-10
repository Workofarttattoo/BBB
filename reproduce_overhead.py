
import time
from concurrent.futures import ThreadPoolExecutor

def dummy_task(x):
    return x * x

def test_creation_overhead():
    start = time.time()
    for _ in range(100):
        with ThreadPoolExecutor(max_workers=10) as executor:
            list(executor.map(dummy_task, range(10)))
    end = time.time()
    print(f"With creation: {end - start:.4f}s")

def test_reused_overhead():
    executor = ThreadPoolExecutor(max_workers=10)
    start = time.time()
    for _ in range(100):
        list(executor.map(dummy_task, range(10)))
    end = time.time()
    print(f"Reused: {end - start:.4f}s")
    executor.shutdown()

if __name__ == "__main__":
    test_creation_overhead()
    test_reused_overhead()
