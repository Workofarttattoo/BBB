import unittest
import sys
import os
import json
import sqlite3
from unittest.mock import MagicMock

# Mock dependencies that are missing in the environment
sys.modules['requests'] = MagicMock()
sys.modules['fastapi'] = MagicMock()
sys.modules['fastapi.HTTPException'] = Exception
sys.modules['fastapi.status'] = MagicMock()

# Now import the module under test
from src.blank_business_builder.integrations import SendGridService, BufferService
from src.blank_business_builder.task_queue import task_queue

class TestIntegrationsQueue(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_integration_tasks.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        # We need to monkeypatch the singleton task_queue's db path
        # Note: In a real app, this is tricky. But for test, we can just re-init db with new path?
        # task_queue is a global instance.
        self.original_db_path = task_queue.db_path
        task_queue.db_path = self.db_path
        task_queue._init_db()

    def tearDown(self):
        # Restore original path (though it doesn't matter much for end of test)
        task_queue.db_path = self.original_db_path
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_send_email_queues_task(self):
        service = SendGridService()
        # send_email queues by default
        result = service.send_email("test@example.com", "Subject", "Body")
        self.assertTrue(result)

        # Check queue
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM tasks WHERE task_type='send_email'")
            task = cursor.fetchone()
            # Schema: id, task_type, payload, status, created_at, attempts, last_error
            self.assertIsNotNone(task)
            payload = json.loads(task[2])
            self.assertEqual(payload['to_email'], "test@example.com")

    def test_buffer_create_post_queues_task(self):
        service = BufferService()
        result = service.create_post("profile_123", "Hello World")
        self.assertTrue(result['success'])

        # Check queue
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM tasks WHERE task_type='create_post'")
            task = cursor.fetchone()
            self.assertIsNotNone(task)
            payload = json.loads(task[2])
            self.assertEqual(payload['text'], "Hello World")

if __name__ == '__main__':
    unittest.main()
