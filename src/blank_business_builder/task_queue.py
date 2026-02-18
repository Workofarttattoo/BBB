"""
Resilient Task Queue for Offline/Online handling.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

import sqlite3
import json
import logging
import asyncio
import time
import urllib.request
import urllib.error
from typing import Dict, Any, Callable

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskQueue:
    """
    Persistent task queue backed by SQLite.
    Handles offline queuing and automatic retries when online.
    """

    def __init__(self, db_path="tasks.db"):
        self.db_path = db_path
        self._init_db()
        self.handlers: Dict[str, Callable] = {}
        self.running = False

    def _init_db(self):
        """Initialize the SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at REAL,
                    attempts INTEGER DEFAULT 0,
                    last_error TEXT
                )
            """)

    def register_handler(self, task_type: str, handler: Callable):
        """Register a function to handle a specific task type."""
        self.handlers[task_type] = handler

    def add_task(self, task_type: str, payload: Dict[str, Any]):
        """Add a task to the queue."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO tasks (task_type, payload, created_at) VALUES (?, ?, ?)",
                (task_type, json.dumps(payload), time.time())
            )
        logger.info(f"Queued task: {task_type}")

    async def start_worker(self):
        """Start the background worker to process tasks."""
        if self.running:
            return

        self.running = True
        logger.info("Task Queue Worker Started")

        while self.running:
            try:
                if await self._check_connectivity():
                    await self._process_pending_tasks()
                else:
                    logger.debug("Offline. Waiting for connection...")
            except Exception as e:
                logger.error(f"Error in task worker: {e}")

            await asyncio.sleep(10) # check every 10s

    def stop_worker(self):
        """Stop the background worker."""
        self.running = False

    async def _check_connectivity(self):
        """Check if internet is available."""
        try:
            # Use run_in_executor for blocking urlopen
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: urllib.request.urlopen("http://www.google.com", timeout=3))
            return True
        except (urllib.error.URLError, TimeoutError):
            return False
        except Exception:
            return False

    async def _process_pending_tasks(self):
        """Process pending tasks from the DB."""
        tasks = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            # Retry failed tasks up to 5 times
            cursor = conn.execute(
                "SELECT * FROM tasks WHERE status = 'pending' OR (status = 'failed' AND attempts < 5) ORDER BY created_at ASC LIMIT 10"
            )
            tasks = cursor.fetchall()

        if not tasks:
            return

        logger.info(f"Processing {len(tasks)} pending tasks...")

        for task in tasks:
            task_id = task['id']
            task_type = task['task_type']
            payload = json.loads(task['payload'])
            handler = self.handlers.get(task_type)

            if not handler:
                logger.error(f"No handler for task type: {task_type}")
                self._update_task_status(task_id, 'failed', "No handler registered")
                continue

            # Mark as processing (optional, but good for locks if multiple workers)
            # self._update_task_status(task_id, 'processing')

            try:
                # Handlers can be async or sync
                if asyncio.iscoroutinefunction(handler):
                    await handler(payload)
                else:
                    await asyncio.to_thread(handler, payload)

                self._update_task_status(task_id, 'completed')
                logger.info(f"Task {task_id} ({task_type}) completed")

            except Exception as e:
                logger.error(f"Task {task_id} failed: {e}")
                self._update_task_status(task_id, 'failed', str(e), increment_attempt=True)

    def _update_task_status(self, task_id, status, error=None, increment_attempt=False):
        with sqlite3.connect(self.db_path) as conn:
            if increment_attempt:
                conn.execute(
                    "UPDATE tasks SET status = ?, last_error = ?, attempts = attempts + 1 WHERE id = ?",
                    (status, error, task_id)
                )
            else:
                conn.execute(
                    "UPDATE tasks SET status = ?, last_error = ? WHERE id = ?",
                    (status, error, task_id)
                )

    def get_queue_status(self):
        """Get stats about the queue."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status")
            return dict(cursor.fetchall())

# Singleton instance
task_queue = TaskQueue()
