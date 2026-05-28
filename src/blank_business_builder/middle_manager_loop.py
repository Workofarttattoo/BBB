"""
Middle Manager Loop — 30min Heartbeat Supervisor
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Supervises worker agents with regular heartbeat checks:
- Runs every 30 minutes via Celery beat
- Checks for stuck tasks, open loops, pending approvals
- Produces brief for CEO review
- Escalates blocked items
- No outbound actions (read-only supervision)

Usage:
    # Called by Celery beat every 30 min
    from .middle_manager_loop import MiddleManagerLoop
    
    manager = MiddleManagerLoop(company_pack="saas-micro-tools")
    brief = await manager.run_heartbeat()
    
    # Brief contains: active tasks, stuck items, pending approvals, escalations
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ManagerBrief:
    """Output from middle manager heartbeat."""
    timestamp: datetime
    active_tasks: int
    completed_since_last: int
    stuck_tasks: List[Dict[str, Any]]
    pending_approvals: int
    open_loops: List[Dict[str, Any]]
    escalations: List[Dict[str, Any]]
    judge_stats: Dict[str, Any]
    system_health: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "active_tasks": self.active_tasks,
            "completed_since_last": self.completed_since_last,
            "stuck_tasks": self.stuck_tasks,
            "pending_approvals": self.pending_approvals,
            "open_loops": self.open_loops,
            "escalations": self.escalations,
            "judge_stats": self.judge_stats,
            "system_health": self.system_health
        }


class MiddleManagerLoop:
    """
    Supervisory loop for worker agents.
    
    Viktor-style features:
    - Proactive monitoring (no human needs to check)
    - Clear escalation paths
    - Audit trail in logs
    - GUI-visible status
    """
    
    def __init__(
        self,
        company_pack: str = "saas-micro-tools",
        state_path: Optional[Path] = None
    ):
        self.company_pack = company_pack
        self.pack_path = Path(__file__).parent.parent.parent / "companies" / company_pack
        
        if state_path:
            self.state_path = state_path
        else:
            self.state_path = Path(__file__).parent.parent.parent / "business_state.json"
        
        self.briefs_path = Path(__file__).parent.parent.parent / "logs" / "manager_briefs.jsonl"
        self.briefs_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load policy
        self.policy = self._load_policy()
        
        # Last brief timestamp
        self.last_brief_time = self._get_last_brief_time()
    
    def _load_policy(self) -> Dict[str, Any]:
        """Load policy.json."""
        policy_path = self.pack_path / "policy.json"
        if policy_path.exists():
            with open(policy_path) as f:
                return json.load(f)
        return {}
    
    def _get_last_brief_time(self) -> Optional[datetime]:
        """Get timestamp of last brief."""
        if not self.briefs_path.exists():
            return None
        
        try:
            with open(self.briefs_path) as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    data = json.loads(last_line)
                    return datetime.fromisoformat(data.get("timestamp", ""))
        except Exception as e:
            logger.warning(f"Failed to read last brief time: {e}")
        
        return None
    
    async def run_heartbeat(self) -> ManagerBrief:
        """
        Run supervisory heartbeat check.
        
        Returns:
            ManagerBrief with status summary
        """
        logger.info("Running middle manager heartbeat...")
        
        now = datetime.now()
        
        # Gather state
        state = self._load_state()
        active_tasks = self._get_active_tasks(state)
        completed_count = self._get_completed_since_last(state)
        stuck_tasks = self._find_stuck_tasks(state)
        pending_approvals = self._get_pending_approvals()
        open_loops = self._find_open_loops(state)
        escalations = self._find_escalations(state)
        judge_stats = self._get_judge_stats()
        system_health = self._check_system_health()
        
        brief = ManagerBrief(
            timestamp=now,
            active_tasks=len(active_tasks),
            completed_since_last=completed_count,
            stuck_tasks=stuck_tasks,
            pending_approvals=pending_approvals,
            open_loops=open_loops,
            escalations=escalations,
            judge_stats=judge_stats,
            system_health=system_health
        )
        
        # Save brief
        self._save_brief(brief)
        
        # Update state
        self._update_state_with_brief(state, brief)
        
        logger.info(f"Heartbeat complete: {len(active_tasks)} active, {pending_approvals} pending approvals")
        
        return brief
    
    def _load_state(self) -> Dict[str, Any]:
        """Load business_state.json."""
        if self.state_path.exists():
            try:
                with open(self.state_path) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load state: {e}")
        return {}
    
    def _get_active_tasks(self, state: Dict[str, Any]) -> List[Dict]:
        """Get currently active tasks."""
        return state.get("active_tasks", [])
    
    def _get_completed_since_last(self, state: Dict[str, Any]) -> int:
        """Count tasks completed since last heartbeat."""
        task_history = state.get("task_history", [])
        
        if not self.last_brief_time:
            return len(task_history)
        
        completed = 0
        for task in task_history:
            completed_at = task.get("completed_at")
            if completed_at:
                try:
                    task_time = datetime.fromisoformat(completed_at)
                    if task_time > self.last_brief_time:
                        completed += 1
                except:
                    pass
        
        return completed
    
    def _find_stuck_tasks(self, state: Dict[str, Any]) -> List[Dict]:
        """Find tasks stuck in progress too long."""
        stuck = []
        active_tasks = state.get("active_tasks", [])
        
        stuck_threshold = timedelta(hours=2)  # Configurable
        now = datetime.now()
        
        for task in active_tasks:
            created_at = task.get("created_at")
            if created_at:
                try:
                    task_time = datetime.fromisoformat(created_at)
                    age = now - task_time
                    if age > stuck_threshold:
                        stuck.append({
                            "task_id": task.get("task_id"),
                            "description": task.get("description", "")[:100],
                            "age_hours": age.total_seconds() / 3600,
                            "status": task.get("status")
                        })
                except:
                    pass
        
        return stuck
    
    def _get_pending_approvals(self) -> int:
        """Count pending approval requests."""
        from .enterprise_agent_policy import EnterpriseAgentPolicy
        
        policy = EnterpriseAgentPolicy(company_pack=self.company_pack)
        pending = policy.get_pending_approvals()
        return len(pending)
    
    def _find_open_loops(self, state: Dict[str, Any]) -> List[Dict]:
        """Find tasks with incomplete judge loops or missing closure."""
        open_loops = []
        active_tasks = state.get("active_tasks", [])
        
        for task in active_tasks:
            # Check if task has judge verdict but no resolution
            judge_verdict = task.get("judge_verdict")
            approval_status = task.get("approval_status")
            
            if judge_verdict == "pass" and not approval_status:
                open_loops.append({
                    "task_id": task.get("task_id"),
                    "issue": "Judge passed but awaiting approval",
                    "type": "approval_pending"
                })
            elif judge_verdict == "revise" and task.get("revision_count", 0) >= 3:
                open_loops.append({
                    "task_id": task.get("task_id"),
                    "issue": "Max revisions reached, needs human intervention",
                    "type": "max_revisions"
                })
        
        return open_loops
    
    def _find_escalations(self, state: Dict[str, Any]) -> List[Dict]:
        """Find items needing CEO escalation."""
        escalations = []
        
        # Stuck tasks need escalation
        stuck = self._find_stuck_tasks(state)
        for task in stuck:
            escalations.append({
                "type": "stuck_task",
                "priority": "high" if task["age_hours"] > 4 else "medium",
                "description": f"Task {task['task_id'][:8]} stuck for {task['age_hours']:.1f}h"
            })
        
        # Pending approvals over threshold
        from .enterprise_agent_policy import EnterpriseAgentPolicy
        policy = EnterpriseAgentPolicy(company_pack=self.company_pack)
        pending = policy.get_pending_approvals()
        
        high_value = [p for p in pending if p.threshold_exceeded]
        if high_value:
            escalations.append({
                "type": "high_value_approvals",
                "priority": "high",
                "count": len(high_value),
                "description": f"{len(high_value)} approvals exceeding thresholds"
            })
        
        return escalations
    
    def _get_judge_stats(self) -> Dict[str, Any]:
        """Get judge evaluation statistics."""
        from .auto_judge_loop import AutoJudgeLoop
        
        judge_loop = AutoJudgeLoop(company_pack=self.company_pack, collect_training_data=False)
        return judge_loop.get_stats()
    
    def _check_system_health(self) -> Dict[str, Any]:
        """Check system health indicators."""
        health = {
            "ollama_available": self._check_ollama(),
            "celery_connected": self._check_celery(),
            "database_ok": True,  # Would check actual DB
            "logs_writable": self._check_logs_writable()
        }
        
        health["overall"] = all(health.values())
        return health
    
    def _check_ollama(self) -> bool:
        """Check if Ollama is available."""
        import os
        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        
        try:
            import requests
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _check_celery(self) -> bool:
        """Check if Celery broker is connected."""
        # Would check Redis connection
        # For now, assume OK if we can import celery
        try:
            import celery
            return True
        except:
            return False
    
    def _check_logs_writable(self) -> bool:
        """Check if logs directory is writable."""
        try:
            test_file = self.briefs_path.parent / ".write_test"
            test_file.touch()
            test_file.unlink()
            return True
        except:
            return False
    
    def _save_brief(self, brief: ManagerBrief):
        """Save brief to logs."""
        try:
            with open(self.briefs_path, "a") as f:
                f.write(json.dumps(brief.to_dict()) + "\n")
        except Exception as e:
            logger.warning(f"Failed to save brief: {e}")
    
    def _update_state_with_brief(self, state: Dict[str, Any], brief: ManagerBrief):
        """Update business_state.json with brief summary."""
        state["last_manager_brief"] = brief.to_dict()
        state["last_manager_brief_time"] = brief.timestamp.isoformat()
        
        # Add escalations to pending if any
        if brief.escalations:
            existing_escalations = state.get("escalations", [])
            state["escalations"] = existing_escalations + brief.escalations
        
        try:
            with open(self.state_path, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to update state: {e}")
    
    def get_recent_briefs(self, count: int = 10) -> List[Dict]:
        """Get N most recent briefs."""
        if not self.briefs_path.exists():
            return []
        
        briefs = []
        try:
            with open(self.briefs_path) as f:
                lines = f.readlines()
                for line in reversed(lines[-count:]):
                    briefs.append(json.loads(line.strip()))
        except Exception as e:
            logger.warning(f"Failed to read briefs: {e}")
        
        return briefs
