import unittest
import asyncio
import sqlite3
import os
import json
from unittest.mock import MagicMock
from src.blank_business_builder.ech0_service import ECH0Service
from src.blank_business_builder.task_queue import task_queue

class TestECH0TaskQueue(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_ech0_queue.db"
        self.original_db_path = task_queue.db_path
        task_queue.db_path = self.db_path
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        task_queue._init_db()
        self.service = ECH0Service()

    def tearDown(self):
        task_queue.db_path = self.original_db_path
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_send_email_queues_task(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(
            self.service.send_email("from@example.com", "to@example.com", "Subject", "Body")
        )
        loop.close()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM tasks WHERE task_type='send_email'")
            task = cursor.fetchone()
            self.assertIsNotNone(task)
            payload = json.loads(task[2])
            self.assertEqual(payload['to_email'], "to@example.com")
            self.assertEqual(payload['subject'], "Subject")

if __name__ == '__main__':
    unittest.main()
