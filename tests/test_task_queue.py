import unittest
import asyncio
import sqlite3
import os
import json
from src.blank_business_builder.task_queue import TaskQueue

class TestTaskQueue(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_tasks.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.queue = TaskQueue(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_add_task(self):
        self.queue.add_task("test_task", {"foo": "bar"})
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM tasks")
            rows = cursor.fetchall()
            self.assertEqual(len(rows), 1)
            # Schema: id, task_type, payload, status, created_at, attempts, last_error
            self.assertEqual(rows[0][1], "test_task")
            self.assertEqual(json.loads(rows[0][2]), {"foo": "bar"})
            self.assertEqual(rows[0][3], "pending")

    def test_process_task(self):
        # Mock handler
        result = []
        async def handler(payload):
            result.append(payload["foo"])

        self.queue.register_handler("test_task", handler)
        self.queue.add_task("test_task", {"foo": "bar"})

        # Manually trigger processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(self.queue._process_pending_tasks())
        loop.close()

        self.assertEqual(result, ["bar"])

        # Check status
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT status FROM tasks")
            status = cursor.fetchone()[0]
            self.assertEqual(status, "completed")

if __name__ == '__main__':
    unittest.main()
