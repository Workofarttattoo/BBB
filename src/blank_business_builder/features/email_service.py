"""
Email service for marketing and sales communications.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations
from typing import List

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    class SendGridAPIClient:
        def __init__(self, *args, **kwargs): pass
        def send(self, *args, **kwargs): return type('Response', (), {'status_code': 202})()
    class Mail:
        def __init__(self, *args, **kwargs): pass
    SENDGRID_AVAILABLE = False

from ..ech0_service import ECH0Service

class EmailService:
    """
    Email service for sending marketing and sales emails.
    """

    def __init__(self, api_key: str):
        if SENDGRID_AVAILABLE:
            self.client = SendGridAPIClient(api_key)
        else:
            self.client = None
        self.ech0_service = ECH0Service()

    async def send_email(
        self,
        from_email: str,
        to_emails: List[str],
        subject: str,
        html_content: str,
        *,
        business_name: str = "default",
        role: str = "marketer",
        approval_id: str | None = None,
        skip_gate: bool = False,
    ) -> bool:
        """
        Send an email using SendGrid.
        """
        if not skip_gate:
            from ..approval_gates import GateAction, gate_from_policy
            from ..enterprise_agent_policy import Capability, resolve_business_policy

            policy = resolve_business_policy(business_name).policy_for_role(role)
            gate_from_policy(
                mode_requires_approval=policy.requires_approval_before_side_effect(
                    Capability.EMAIL_SEND
                ),
                action=GateAction.EMAIL_SEND,
                business_name=business_name,
                role=role,
                approval_id=approval_id,
                metadata={"subject": subject, "to": to_emails},
                force_manual=policy.is_manual_only(Capability.EMAIL_SEND),
            )
        try:
            # Try sending with ECH0 first
            return await self.ech0_service.send_email(from_email, to_emails[0], subject, html_content)
        except Exception:
            # Fallback to SendGrid
            if self.client and Mail:
                message = Mail(
                    from_email=from_email,
                    to_emails=to_emails,
                    subject=subject,
                    html_content=html_content
                )
                try:
                    response = self.client.send(message)
                    return response.status_code == 202
                except Exception as e:
                    print(f"Error sending email: {e}")
                    return False
            else:
                print("Error: SendGrid not available")
                return False
