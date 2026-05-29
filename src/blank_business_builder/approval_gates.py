"""
Approval gates for outbound integrations (SendGrid, Stripe, Apollo bulk).

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class GateAction(str, Enum):
    EMAIL_SEND = "email_send"
    EMAIL_CAMPAIGN = "email_campaign"
    PAYMENT_CHARGE = "payment_charge"
    APOLLO_BULK = "apollo_bulk"
    LEAD_INGEST = "lead_ingest"


@dataclass
class ApprovalRecord:
    approval_id: str
    action: GateAction
    business_name: str
    role: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    requested_by: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "action": self.action.value,
            "business_name": self.business_name,
            "role": self.role,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "metadata": self.metadata,
            "requested_by": self.requested_by,
        }


class ApprovalGateError(Exception):
    """Raised when a side-effect is blocked pending approval."""

    def __init__(self, message: str, approval_id: Optional[str] = None):
        super().__init__(message)
        self.approval_id = approval_id


class ApprovalStore:
    """In-process approval store (replace with DB/Redis in production)."""

    _lock = threading.Lock()
    _records: Dict[str, ApprovalRecord] = {}

    @classmethod
    def create(
        cls,
        action: GateAction,
        business_name: str,
        role: str,
        metadata: Optional[Dict[str, Any]] = None,
        requested_by: Optional[str] = None,
    ) -> ApprovalRecord:
        record = ApprovalRecord(
            approval_id=str(uuid.uuid4()),
            action=action,
            business_name=business_name,
            role=role,
            metadata=metadata or {},
            requested_by=requested_by,
        )
        with cls._lock:
            cls._records[record.approval_id] = record
        return record

    @classmethod
    def get(cls, approval_id: str) -> Optional[ApprovalRecord]:
        with cls._lock:
            return cls._records.get(approval_id)

    @classmethod
    def resolve(cls, approval_id: str, status: ApprovalStatus) -> Optional[ApprovalRecord]:
        with cls._lock:
            record = cls._records.get(approval_id)
            if not record:
                return None
            record.status = status
            record.resolved_at = datetime.utcnow()
            return record

    @classmethod
    def list_pending(cls, business_name: Optional[str] = None) -> List[ApprovalRecord]:
        with cls._lock:
            items = list(cls._records.values())
        pending = [r for r in items if r.status == ApprovalStatus.PENDING]
        if business_name:
            pending = [r for r in pending if r.business_name == business_name]
        return sorted(pending, key=lambda r: r.created_at)


def assert_approved_or_raise(
    action: GateAction,
    business_name: str,
    role: str,
    approval_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Block side-effect unless approval_id references an approved record for this action.
    """
    if approval_id:
        record = ApprovalStore.get(approval_id)
        if (
            record
            and record.status == ApprovalStatus.APPROVED
            and record.action == action
            and record.business_name == business_name
        ):
            return
        if record and record.status == ApprovalStatus.PENDING:
            raise ApprovalGateError(
                f"Approval {approval_id} is still pending for {action.value}.",
                approval_id=approval_id,
            )
        raise ApprovalGateError(
            f"Invalid or rejected approval {approval_id} for {action.value}.",
            approval_id=approval_id,
        )

    pending = ApprovalStore.create(
        action=action,
        business_name=business_name,
        role=role,
        metadata=metadata,
    )
    raise ApprovalGateError(
        f"{action.value} requires board approval. Created approval_id={pending.approval_id}.",
        approval_id=pending.approval_id,
    )


def gate_from_policy(
    *,
    mode_requires_approval: bool,
    action: GateAction,
    business_name: str,
    role: str,
    approval_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    force_manual: bool = False,
) -> None:
    """Combine enterprise policy mode with approval store."""
    if force_manual:
        raise ApprovalGateError(
            f"{action.value} is manual-only for role {role}. Use the BBB GUI or board workflow."
        )
    if mode_requires_approval:
        assert_approved_or_raise(
            action,
            business_name,
            role,
            approval_id=approval_id,
            metadata=metadata,
        )
