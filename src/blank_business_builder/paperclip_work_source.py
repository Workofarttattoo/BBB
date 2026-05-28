"""
Paperclip Work Source Sync — Issue → Task Queue
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Synchronizes Paperclip issues with BBB task queue:
- Fetch issues by label (bbb:execute, plan:*, judge:*, echo:strategy, human:apollo)
- Route to appropriate agent based on label
- Update issue status on completion
- Post comments with results

Usage:
    sync = PaperclipWorkSourceSync()
    issues = await sync.fetch_issues(label="bbb:execute")
    
    for issue in issues:
        task = sync.create_task(issue)
        # Enqueue to AutonomousBusinessOrchestrator
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger(__name__)


@dataclass
class PaperclipIssue:
    """Paperclip issue representation."""
    issue_id: str
    title: str
    description: str
    labels: List[str]
    state: str  # open | closed
    created_at: datetime
    updated_at: datetime
    assignee: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "issue_id": self.issue_id,
            "title": self.title,
            "description": self.description,
            "labels": self.labels,
            "state": self.state,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "assignee": self.assignee,
            "metadata": self.metadata
        }


@dataclass
class LabelRouting:
    """Label routing configuration."""
    label: str
    allowed_agents: List[str]
    action: str
    description: str


class PaperclipWorkSourceSync:
    """
    Synchronize Paperclip issues with BBB task queue.
    
    Viktor-style features:
    - Automatic label-based routing
    - Respects human gates (human:apollo never auto-executes)
    - Posts results back as comments
    - Closes issues only after judge pass + human review (G3)
    """
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_token: Optional[str] = None,
        config_path: Optional[Path] = None
    ):
        self.api_url = api_url or os.getenv("PAPERCLIP_API_URL", "http://127.0.0.1:3100")
        self.api_token = api_token or os.getenv("PAPERCLIP_API_TOKEN", "")
        
        # Load label routing config
        if config_path:
            self.config_path = config_path
        else:
            self.config_path = Path(__file__).parent.parent.parent / "config" / "enterprise" / "paperclip_issue_labels.json"
        
        self.label_routing = self._load_label_routing()
        
        # Has API access?
        self.has_api = bool(self.api_url and self.api_token)
        
        if not self.has_api:
            logger.warning("Paperclip API not configured (PAPERCLIP_API_URL/TOKEN). GUI paste mode only.")
    
    def _load_label_routing(self) -> Dict[str, LabelRouting]:
        """Load label routing from config."""
        if not self.config_path.exists():
            logger.warning(f"Label routing config not found: {self.config_path}")
            return {}
        
        try:
            with open(self.config_path) as f:
                config = json.load(f)
            
            routing = {}
            for label, data in config.get("labels", {}).items():
                routing[label] = LabelRouting(
                    label=label,
                    allowed_agents=data.get("allowed_agents", []),
                    action=data.get("action", ""),
                    description=data.get("description", "")
                )
            
            return routing
        except Exception as e:
            logger.error(f"Failed to load label routing: {e}")
            return {}
    
    async def fetch_issues(self, label: Optional[str] = None, state: str = "open") -> List[PaperclipIssue]:
        """
        Fetch issues from Paperclip API.
        
        Args:
            label: Filter by label (None = all)
            state: Filter by state (open | closed)
            
        Returns:
            List of PaperclipIssue objects
        """
        if not self.has_api:
            logger.info("No Paperclip API access - use GUI paste mode")
            return []
        
        # Build query
        params = {"state": state}
        if label:
            params["label"] = label
        
        try:
            import aiohttp
            
            headers = {"Authorization": f"Bearer {self.api_token}"} if self.api_token else {}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/api/issues",
                    params=params,
                    headers=headers,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return [self._parse_issue(issue_data) for issue_data in data.get("issues", [])]
                    else:
                        logger.error(f"Paperclip API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.exception(f"Failed to fetch issues: {e}")
            return []
    
    def _parse_issue(self, data: Dict[str, Any]) -> PaperclipIssue:
        """Parse API response into PaperclipIssue."""
        return PaperclipIssue(
            issue_id=data.get("id", str(uuid.uuid4())),
            title=data.get("title", "Untitled"),
            description=data.get("description", ""),
            labels=data.get("labels", []),
            state=data.get("state", "open"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
            assignee=data.get("assignee"),
            metadata=data.get("metadata", {})
        )
    
    def route_issue(self, issue: PaperclipIssue) -> Optional[Dict[str, Any]]:
        """
        Route issue to appropriate agent based on labels.
        
        Returns:
            Task dict for orchestrator, or None if should not execute
        """
        # Find matching label
        matched_routing = None
        matched_label = None
        
        for label in issue.labels:
            if label in self.label_routing:
                matched_routing = self.label_routing[label]
                matched_label = label
                break
        
        if not matched_routing:
            # Use default
            default_routing = self.label_routing.get("bbb:execute")
            if not default_routing:
                logger.warning(f"No routing for issue {issue.issue_id} with labels {issue.labels}")
                return None
            matched_routing = default_routing
            matched_label = "bbb:execute"
        
        # Check if human gate
        if matched_routing.action == "escalate_to_human":
            logger.info(f"Issue {issue.issue_id} requires human action ({matched_label})")
            return None
        
        # Check if planner-only (creates child issues, doesn't execute)
        if matched_routing.action in ["create_child_issues", "create_milestone"]:
            logger.info(f"Issue {issue.issue_id} is planning task ({matched_label})")
            # Would create child bbb:execute issues here
            return None
        
        # Determine role from issue
        role = self._infer_role(issue, matched_routing)
        
        # Create task
        return {
            "task_id": str(uuid.uuid4()),
            "source": "paperclip",
            "source_issue_id": issue.issue_id,
            "role": role,
            "description": issue.description,
            "title": issue.title,
            "labels": issue.labels,
            "priority": 5,
            "requires_approval": self._check_requires_approval(role)
        }
    
    def _infer_role(self, issue: PaperclipIssue, routing: LabelRouting) -> str:
        """Infer agent role from issue content and labels."""
        # If routing specifies allowed agents, pick first
        if routing.allowed_agents:
            # Map to standard roles
            agent_map = {
                "sales": "sales",
                "engineer": "engineer",
                "marketer": "marketer",
                "support": "support",
                "researcher": "researcher",
                "planner": "meta_manager",
                "meta_manager": "meta_manager",
                "executive": "executive",
                "ech0_overseer": "executive"
            }
            for agent in routing.allowed_agents:
                if agent in agent_map:
                    return agent_map[agent]
        
        # Infer from labels
        label_to_role = {
            "sales": "sales",
            "engineering": "engineer",
            "marketing": "marketer",
            "support": "support",
            "research": "researcher"
        }
        
        for label in issue.labels:
            label_lower = label.lower()
            for key, role in label_to_role.items():
                if key in label_lower:
                    return role
        
        # Default to sales for bbb:execute
        return "sales"
    
    def _check_requires_approval(self, role: str) -> bool:
        """Check if role requires approval gate."""
        # Sales always needs approval for outbound email
        if role == "sales":
            return True
        
        # Engineer needs approval for PRs
        if role == "engineer":
            return True
        
        return False
    
    async def post_comment(self, issue_id: str, comment: str):
        """Post comment to Paperclip issue."""
        if not self.has_api:
            logger.info(f"Would post comment to {issue_id}: {comment[:100]}...")
            return
        
        try:
            import aiohttp
            
            headers = {"Authorization": f"Bearer {self.api_token}"} if self.api_token else {}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/api/issues/{issue_id}/comments",
                    json={"body": comment},
                    headers=headers,
                    timeout=30
                ) as response:
                    if response.status in [200, 201]:
                        logger.info(f"Posted comment to issue {issue_id}")
                    else:
                        logger.error(f"Failed to post comment: {response.status}")
                        
        except Exception as e:
            logger.exception(f"Failed to post comment: {e}")
    
    async def close_issue(self, issue_id: str, comment: Optional[str] = None):
        """Close Paperclip issue with optional final comment."""
        if comment:
            await self.post_comment(issue_id, comment)
        
        if not self.has_api:
            logger.info(f"Would close issue {issue_id}")
            return
        
        try:
            import aiohttp
            
            headers = {"Authorization": f"Bearer {self.api_token}"} if self.api_token else {}
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    f"{self.api_url}/api/issues/{issue_id}",
                    json={"state": "closed"},
                    headers=headers,
                    timeout=30
                ) as response:
                    if response.status in [200, 201]:
                        logger.info(f"Closed issue {issue_id}")
                    else:
                        logger.error(f"Failed to close issue: {response.status}")
                        
        except Exception as e:
            logger.exception(f"Failed to close issue: {e}")
    
    def parse_paste(self, paste_text: str) -> List[PaperclipIssue]:
        """
        Parse JSON paste from GUI into issues.
        
        This is for when API is not available - user copy-pastes issue JSON.
        """
        try:
            data = json.loads(paste_text)
            
            # Handle single issue or list
            if isinstance(data, dict):
                data = [data]
            
            return [self._parse_issue(issue_data) for issue_data in data]
        except Exception as e:
            logger.error(f"Failed to parse paste: {e}")
            return []
    
    def get_routing_help(self) -> str:
        """Get human-readable routing help text."""
        lines = ["Paperclip Label Routing:", ""]
        
        for label, routing in self.label_routing.items():
            agents = ", ".join(routing.allowed_agents) or "none (human only)"
            lines.append(f"- `{label}`: {routing.description}")
            lines.append(f"  Action: {routing.action}")
            lines.append(f"  Agents: {agents}")
            lines.append("")
        
        return "\n".join(lines)
