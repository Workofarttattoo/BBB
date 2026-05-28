"""
Task Locks — Planner vs Execute Deduplication
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Prevents duplicate execution when planner creates child issues:
- Track which tasks are being executed
- Prevent planner from creating duplicates of in-flight tasks
- Allow executor to check if task is already claimed

Usage:
    locks = TaskLockManager()
    
    # Before executing
    if locks.acquire_lock(task_id, "executor"):
        # Safe to execute
        pass
    
    # Before creating child task
    if not locks.is_locked(child_task_description):
        # Safe to create
        pass
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import threading

logger = logging.getLogger(__name__)


@dataclass
class TaskLock:
    """Lock record for a task."""
    task_id: str
    locked_by: str  # "planner" | "executor" | role name
    acquired_at: datetime
    expires_at: datetime
    description_hash: str  # For dedup by description
    
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "locked_by": self.locked_by,
            "acquired_at": self.acquired_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "description_hash": self.description_hash
        }


class TaskLockManager:
    """
    Manage task execution locks to prevent duplicates.
    
    Viktor-style features:
    - Automatic expiration (no deadlocks)
    - Hash-based deduplication (catches similar tasks)
    - Thread-safe for concurrent access
    - Persistent state across restarts
    """
    
    def __init__(
        self,
        state_path: Optional[Path] = None,
        lock_timeout_minutes: int = 30
    ):
        if state_path:
            self.state_path = state_path
        else:
            self.state_path = Path(__file__).parent.parent.parent / "logs" / "task_locks.json"
        
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.lock_timeout = timedelta(minutes=lock_timeout_minutes)
        self._locks: Dict[str, TaskLock] = {}
        self._lock = threading.Lock()  # Thread safety
        
        # Load existing state
        self._load_state()
    
    def _load_state(self):
        """Load locks from disk."""
        if self.state_path.exists():
            try:
                with open(self.state_path) as f:
                    data = json.load(f)
                
                self._locks = {
                    task_id: TaskLock(
                        task_id=lock_data["task_id"],
                        locked_by=lock_data["locked_by"],
                        acquired_at=datetime.fromisoformat(lock_data["acquired_at"]),
                        expires_at=datetime.fromisoformat(lock_data["expires_at"]),
                        description_hash=lock_data["description_hash"]
                    )
                    for task_id, lock_data in data.get("locks", {}).items()
                }
                
                # Clean expired on load
                self._cleanup_expired()
                
                logger.debug(f"Loaded {len(self._locks)} task locks")
            except Exception as e:
                logger.warning(f"Failed to load task locks: {e}")
                self._locks = {}
    
    def _save_state(self):
        """Save locks to disk."""
        try:
            data = {
                "locks": {task_id: lock.to_dict() for task_id, lock in self._locks.items()},
                "updated_at": datetime.now().isoformat()
            }
            
            with open(self.state_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save task locks: {e}")
    
    def _cleanup_expired(self):
        """Remove expired locks."""
        expired = [
            task_id for task_id, lock in self._locks.items()
            if lock.is_expired()
        ]
        
        for task_id in expired:
            del self._locks[task_id]
        
        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired locks")
            self._save_state()
    
    def _hash_description(self, description: str) -> str:
        """Create hash of task description for dedup."""
        import hashlib
        # Normalize whitespace
        normalized = " ".join(description.lower().split())
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    def acquire_lock(
        self,
        task_id: str,
        locked_by: str,
        description: Optional[str] = None
    ) -> bool:
        """
        Try to acquire lock for task.
        
        Args:
            task_id: Unique task identifier
            locked_by: Who is acquiring (role or "planner"/"executor")
            description: Optional description for hash-based dedup
            
        Returns:
            True if lock acquired, False if already locked
        """
        with self._lock:
            # Check expired first
            self._cleanup_expired()
            
            # Check if task already locked
            if task_id in self._locks:
                existing = self._locks[task_id]
                if not existing.is_expired():
                    logger.debug(f"Task {task_id} already locked by {existing.locked_by}")
                    return False
            
            # Check description hash dedup
            if description:
                desc_hash = self._hash_description(description)
                for existing in self._locks.values():
                    if existing.description_hash == desc_hash and not existing.is_expired():
                        logger.debug(f"Similar task already locked: {description[:50]}...")
                        return False
            
            # Acquire lock
            self._locks[task_id] = TaskLock(
                task_id=task_id,
                locked_by=locked_by,
                acquired_at=datetime.now(),
                expires_at=datetime.now() + self.lock_timeout,
                description_hash=self._hash_description(description) if description else ""
            )
            
            self._save_state()
            logger.debug(f"Acquired lock for task {task_id} by {locked_by}")
            return True
    
    def release_lock(self, task_id: str) -> bool:
        """
        Release lock for task.
        
        Returns:
            True if released, False if not found
        """
        with self._lock:
            if task_id in self._locks:
                del self._locks[task_id]
                self._save_state()
                logger.debug(f"Released lock for task {task_id}")
                return True
            
            logger.debug(f"No lock found for task {task_id}")
            return False
    
    def is_locked(self, task_id: str) -> bool:
        """Check if task is currently locked."""
        with self._lock:
            if task_id in self._locks:
                lock = self._locks[task_id]
                if not lock.is_expired():
                    return True
                else:
                    # Expired - clean up
                    del self._locks[task_id]
                    self._save_state()
            
            return False
    
    def is_similar_task_locked(self, description: str) -> bool:
        """Check if a similar task (by description hash) is locked."""
        desc_hash = self._hash_description(description)
        
        with self._lock:
            for lock in self._locks.values():
                if lock.description_hash == desc_hash and not lock.is_expired():
                    return True
            
            return False
    
    def get_lock(self, task_id: str) -> Optional[TaskLock]:
        """Get lock details for task."""
        with self._lock:
            lock = self._locks.get(task_id)
            if lock and not lock.is_expired():
                return lock
            return None
    
    def get_all_active_locks(self) -> List[TaskLock]:
        """Get all active (non-expired) locks."""
        with self._lock:
            self._cleanup_expired()
            return list(self._locks.values())
    
    def extend_lock(self, task_id: str, additional_minutes: int = 30) -> bool:
        """Extend lock expiration time."""
        with self._lock:
            if task_id in self._locks:
                lock = self._locks[task_id]
                if not lock.is_expired():
                    lock.expires_at = datetime.now() + timedelta(minutes=additional_minutes)
                    self._save_state()
                    logger.debug(f"Extended lock for task {task_id}")
                    return True
            
            return False
    
    def clear_all(self):
        """Clear all locks (use with caution)."""
        with self._lock:
            self._locks.clear()
            self._save_state()
            logger.info("Cleared all task locks")
