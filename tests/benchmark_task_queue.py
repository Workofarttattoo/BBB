import asyncio
import sqlite3
import time
import os

from blank_business_builder.task_queue import task_queue

def setup_db(db_path, num_tasks=1000):
    if os.path.exists(db_path):
        os.remove(db_path)

    task_queue.db_path = db_path
    task_queue._init_db()

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        for i in range(num_tasks):
            status = 'pending' if i % 2 == 0 else 'completed'
            cursor.execute(
                "INSERT INTO tasks (task_type, payload, status, created_at) VALUES (?, ?, ?, ?)",
                ('test_task', '{}', status, time.time() - i)
            )
        conn.commit()

async def benchmark_process_pending(iterations=100):
    start_time = time.perf_counter()
    for _ in range(iterations):
        tasks = []
        with sqlite3.connect(task_queue.db_path) as conn:
            conn.row_factory = sqlite3.Row
            # Retry failed tasks up to 5 times
            cursor = conn.execute(
                "SELECT * FROM tasks WHERE status IN ('pending', 'failed') AND (status != 'failed' OR attempts < 5) ORDER BY created_at ASC LIMIT 10"
            )
            tasks = cursor.fetchall()

    end_time = time.perf_counter()
    return end_time - start_time

if __name__ == "__main__":
    db_path = "benchmark.db"
    setup_db(db_path, num_tasks=10000)

    t = asyncio.run(benchmark_process_pending(500))
    print(f"Time taken to query tasks 500 times: {t:.4f}s")

    if os.path.exists(db_path):
        os.remove(db_path)
