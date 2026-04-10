
import sqlite3
import os
from src.blank_business_builder.task_queue import TaskQueue

def verify_index():
    # Use a temporary DB file
    db_path = "test_tasks_index.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    try:
        queue = TaskQueue(db_path=db_path)

        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("PRAGMA index_list('tasks')")
            indexes = cursor.fetchall()

            # Format: (seq, name, unique, origin, partial)
            index_names = [idx[1] for idx in indexes]
            print(f"Indexes found: {index_names}")

            if "idx_tasks_status_created" in index_names:
                print("SUCCESS: Index 'idx_tasks_status_created' exists.")
            else:
                print("FAILURE: Index 'idx_tasks_status_created' NOT found.")
                exit(1)

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)

if __name__ == "__main__":
    verify_index()
