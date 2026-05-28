"""
Enterprise Agent Policy — Capability Matrix + Approval Gates
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Defines what agents can do autonomously vs what requires approval:
- Internal drafts: always allowed
- Code sandbox: always allowed
- Outbound email: requires CEO approval
- Bulk CRM ingest: requires CEO approval
- Stripe payments: requires CEO approval

Usage:
    policy = EnterpriseAgentPolicy(company_pack="saas-micro-tools")
    
    if policy.can_execute(role="sales", action="email_draft"):
        # Can draft internally
        pass
    
    if policy.requires_approval(role="sales", action="outbound_email"):
        # Must get CEO approval first
        approval_id = policy.create_approval_request(...)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger(__name__)


@dataclass
class ApprovalRequest:
    """Pending approval request."""
    approval_id: str
    action_type: str
    role: str
    description: str
    payload: Dict[str, Any]
    threshold_exceeded: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # pending | approved | rejected
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "approval_id": self.approval_id,
            "action_type": self.action_type,
            "role": self.role,
            "description": self.description,
            "payload": self.payload,
            "threshold_exceeded": self.threshold_exceeded,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by
        }


class EnterpriseAgentPolicy:
    """
    Capability matrix and approval gate enforcement.
    
    Viktor-style features:
    - Clear capability boundaries
    - Automatic threshold detection
    - Persistent approval queue
    - Audit trail for all approvals
    """
    
    def __init__(self, company_pack: str = "saas-micro-tools"):
        self.company_pack = company_pack
        self.pack_path = Path(__file__).parent.parent.parent / "companies" / company_pack
        
        # Load policy
        self.policy = self._load_policy()
        
        # Approval state
        self.approvals_path = Path(__file__).parent.parent.parent / "logs" / "approvals.json"
        self.approvals_path.parent.mkdir(parents=True, exist_ok=True)
        self._approvals: Dict[str, ApprovalRequest] = {}
        self._load_approvals()
    
    def _load_policy(self) -> Dict[str, Any]:
        """Load policy.json from company pack."""
        policy_path = self.pack_path / "policy.json"
        if policy_path.exists():
            with open(policy_path) as f:
                return json.load(f)
        return {
            "capabilities": {},
            "approval_gates": {}
        }
    
    def _load_approvals(self):
        """Load pending approvals from disk."""
        if self.approvals_path.exists():
            try:
                with open(self.approvals_path) as f:
                    data = json.load(f)
                
                self._approvals = {
                    aid: ApprovalRequest(
                        approval_id=app["approval_id"],
                        action_type=app["action_type"],
                        role=app["role"],
                        description=app["description"],
                        payload=app["payload"],
                        threshold_exceeded=app.get("threshold_exceeded"),
                        created_at=datetime.fromisoformat(app["created_at"]),
                        status=app["status"],
                        resolved_at=datetime.fromisoformat(app["resolved_at"]) if app.get("resolved_at") else None,
                        resolved_by=app.get("resolved_by")
                    )
                    for aid, app in data.get("approvals", {}).items()
                }
                
                logger.debug(f"Loaded {len(self._approvals)} approval requests")
            except Exception as e:
                logger.warning(f"Failed to load approvals: {e}")
                self._approvals = {}
    
    def _save_approvals(self):
        """Save approvals to disk."""
        try:
            data = {
                "approvals": {aid: app.to_dict() for aid, app in self._approvals.items()},
                "updated_at": datetime.now().isoformat()
            }
            
            with open(self.approvals_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save approvals: {e}")
    
    def can_execute(self, role: str, action: str) -> bool:
        """
        Check if action is within agent capabilities.
        
        Args:
            role: Agent role (sales, engineer, etc.)
            action: Action type (email_draft, code_sandbox, etc.)
            
        Returns:
            True if capability exists
        """
        capabilities = self.policy.get("capabilities", {})
        return capabilities.get(action, False)
    
    def requires_approval(self, role: str, action: str, quantity: int = 1, amount_usd: float = 0) -> bool:
        """
        Check if action requires CEO approval.
        
        Args:
            role: Agent role
            action: Action type
            quantity: Number of items (leads, posts, etc.)
            amount_usd: Dollar amount (for payments)
            
        Returns:
            True if approval required
        """
        approval_gates = self.policy.get("approval_gates", {})
        
        if action not in approval_gates:
            return False
        
        gate = approval_gates[action]
        
        if not gate.get("required", False):
            return False
        
        # Check thresholds
        threshold_count = gate.get("threshold_count")
        threshold_usd = gate.get("threshold_usd")
        
        if threshold_count and quantity > threshold_count:
            return True
        
        if threshold_usd and amount_usd > threshold_usd:
            return True
        
        # If no threshold or threshold is 0, always require approval
        return True
    
    def create_approval_request(
        self,
        role: str,
        action: str,
        description: str,
        payload: Dict[str, Any],
        quantity: int = 1,
        amount_usd: float = 0
    ) -> str:
        """
        Create approval request for CEO review.
        
        Args:
            role: Requesting agent role
            action: Action requiring approval
            description: Human-readable description
            payload: Full action payload
            quantity: Optional quantity
            amount_usd: Optional USD amount
            
        Returns:
            approval_id for tracking
        """
        # Determine threshold exceeded
        threshold_exceeded = None
        approval_gates = self.policy.get("approval_gates", {})
        
        if action in approval_gates:
            gate = approval_gates[action]
            if gate.get("threshold_count") and quantity > gate["threshold_count"]:
                threshold_exceeded = f"Quantity {quantity} exceeds limit {gate['threshold_count']}"
            elif gate.get("threshold_usd") and amount_usd > gate["threshold_usd"]:
                threshold_exceeded = f"Amount ${amount_usd} exceeds limit ${gate['threshold_usd']}"
        
        approval = ApprovalRequest(
            approval_id=str(uuid.uuid4()),
            action_type=action,
            role=role,
            description=description,
            payload=payload,
            threshold_exceeded=threshold_exceeded
        )
        
        self._approvals[approval.approval_id] = approval
        self._save_approvals()
        
        logger.info(f"Created approval request {approval.approval_id} for {action}")
        return approval.approval_id
    
    def get_pending_approvals(self) -> List[ApprovalRequest]:
        """Get all pending approval requests."""
        return [
            app for app in self._approvals.values()
            if app.status == "pending"
        ]
    
    def resolve_approval(
        self,
        approval_id: str,
        approved: bool,
        resolved_by: str = "ceo"
    ) -> bool:
        """
        Resolve approval request.
        
        Args:
            approval_id: ID from create_approval_request
            approved: True to approve, False to reject
            resolved_by: Who resolved (usually "ceo")
            
        Returns:
            True if resolved successfully
        """
        if approval_id not in self._approvals:
            logger.warning(f"Approval {approval_id} not found")
            return False
        
        approval = self._approvals[approval_id]
        approval.status = "approved" if approved else "rejected"
        approval.resolved_at = datetime.now()
        approval.resolved_by = resolved_by
        
        self._save_approvals()
        
        logger.info(f"Resolved approval {approval_id}: {'approved' if approved else 'rejected'} by {resolved_by}")
        return True
    
    def get_approval(self, approval_id: str) -> Optional[ApprovalRequest]:
        """Get approval request by ID."""
        return self._approvals.get(approval_id)
    
    def check_and_request_approval(
        self,
        role: str,
        action: str,
        description: str,
        payload: Dict[str, Any],
        quantity: int = 1,
        amount_usd: float = 0
    ) -> tuple:
        """
        Check if approval needed and create request if so.
        
        Returns:
            (requires_approval: bool, approval_id: Optional[str])
        """
        if self.requires_approval(role, action, quantity, amount_usd):
            approval_id = self.create_approval_request(
                role=role,
                action=action,
                description=description,
                payload=payload,
                quantity=quantity,
                amount_usd=amount_usd
            )
            return True, approval_id
        
        return False, None
    
    def get_capability_matrix(self) -> Dict[str, Any]:
        """Get full capability matrix."""
        return {
            "business": self.policy.get("business"),
            "capabilities": self.policy.get("capabilities", {}),
            "approval_gates": self.policy.get("approval_gates", {}),
            "viktor_mode": self.policy.get("viktor_mode", {})
        }
    
    def clear_resolved(self, older_than_days: int = 7):
        """Clear resolved approvals older than N days."""
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=older_than_days)
        
        to_remove = [
            aid for aid, app in self._approvals.items()
            if app.status != "pending" and app.resolved_at and app.resolved_at < cutoff
        ]
        
        for aid in to_remove:
            del self._approvals[aid]
        
        if to_remove:
            self._save_approvals()
            logger.info(f"Cleared {len(to_remove)} old resolved approvals")
