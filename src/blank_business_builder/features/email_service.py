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
    SendGridAPIClient = None
    Mail = None
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
        html_content: str
    ) -> bool:
        """
        Send an email using SendGrid.
        """
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
