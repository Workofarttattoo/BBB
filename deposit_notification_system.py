#!/usr/bin/env python3
"""
Deposit Notification System - Revenue Milestone Alerts
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Monitors revenue and sends SMS/email notifications for:
- Daily deposits
- Milestone achievements ($100K, $1M, $10M, etc.)
- Public offering readiness
- Revenue anomalies
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json

from twilio.rest import Client
import stripe
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


class NotificationType(Enum):
    """Types of revenue notifications."""
    DAILY_DEPOSIT = "daily_deposit"
    MILESTONE = "milestone"
    PUBLIC_OFFERING_READY = "public_offering_ready"
    ANOMALY = "anomaly"
    WEEKLY_SUMMARY = "weekly_summary"


@dataclass
class RevenueNotification:
    """Revenue notification."""
    type: NotificationType
    amount: float
    message: str
    timestamp: datetime
    metadata: Dict[str, Any]


class DepositNotificationSystem:
    """
    Automated deposit notification system.

    Monitors Stripe for deposits and sends alerts via:
    - SMS (Twilio) to 725-224-2617
    - Email to inventor@aios.is and echo@aios.is
    """

    def __init__(
        self,
        stripe_api_key: str,
        twilio_account_sid: str,
        twilio_auth_token: str,
        twilio_from_number: str,
        sendgrid_api_key: str,
        notification_phone: str = "+17252242617",
        notification_emails: List[str] = None
    ):
        # Stripe setup
        stripe.api_key = stripe_api_key

        # Twilio setup
        self.twilio_client = Client(twilio_account_sid, twilio_auth_token)
        self.twilio_from = twilio_from_number
        self.notification_phone = notification_phone

        # SendGrid setup
        self.sendgrid_client = SendGridAPIClient(sendgrid_api_key)
        self.notification_emails = notification_emails or [
            "inventor@aios.is",
            "echo@aios.is"
        ]

        # State tracking
        self.last_deposit_check = datetime.now()
        self.total_revenue = 0.0
        self.milestones_reached = set()
        self.notification_history = []

        # Milestone thresholds
        self.milestones = [
            10_000,      # $10K
            50_000,      # $50K
            100_000,     # $100K
            250_000,     # $250K
            500_000,     # $500K
            1_000_000,   # $1M
            5_000_000,   # $5M
            10_000_000,  # $10M
            50_000_000,  # $50M
            100_000_000, # $100M - Public offering ready
        ]

    async def check_stripe_deposits(self) -> List[Dict[str, Any]]:
        """
        Check Stripe for new deposits/payouts.

        Returns list of new deposits since last check.
        """
        try:
            # Get payouts (actual money hitting bank account)
            payouts = stripe.Payout.list(
                created={'gte': int(self.last_deposit_check.timestamp())},
                limit=100
            )

            new_deposits = []

            for payout in payouts.auto_paging_iter():
                if payout.status == "paid":
                    new_deposits.append({
                        'id': payout.id,
                        'amount': payout.amount / 100,  # Convert cents to dollars
                        'currency': payout.currency,
                        'arrival_date': datetime.fromtimestamp(payout.arrival_date),
                        'description': payout.description or "Stripe payout"
                    })

            self.last_deposit_check = datetime.now()
            return new_deposits

        except Exception as e:
            print(f"Error checking Stripe deposits: {e}")
            return []

    async def check_revenue_milestones(self, current_revenue: float) -> List[float]:
        """
        Check if new revenue milestones have been reached.

        Returns list of newly reached milestones.
        """
        new_milestones = []

        for milestone in self.milestones:
            if current_revenue >= milestone and milestone not in self.milestones_reached:
                self.milestones_reached.add(milestone)
                new_milestones.append(milestone)

        return new_milestones

    async def send_sms_notification(self, message: str) -> bool:
        """Send SMS notification via Twilio."""
        try:
            message = self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_from,
                to=self.notification_phone
            )
            print(f"✅ SMS sent: {message.sid}")
            return True
        except Exception as e:
            print(f"❌ SMS failed: {e}")
            return False

    async def send_email_notification(
        self,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """Send email notification via SendGrid."""
        try:
            for email in self.notification_emails:
                message = Mail(
                    from_email='notifications@flowstatus.work',
                    to_emails=email,
                    subject=subject,
                    plain_text_content=body,
                    html_content=html_body or body
                )

                response = self.sendgrid_client.send(message)
                print(f"✅ Email sent to {email}: {response.status_code}")

            return True
        except Exception as e:
            print(f"❌ Email failed: {e}")
            return False

    async def notify_deposit(self, deposit: Dict[str, Any]) -> None:
        """Send notification for new deposit."""
        amount = deposit['amount']
        date = deposit['arrival_date']

        # SMS notification
        sms_message = f"""
💰 BBB DEPOSIT RECEIVED

Amount: ${amount:,.2f}
Date: {date.strftime('%Y-%m-%d')}

Total Revenue: ${self.total_revenue:,.2f}

- ECH0 Autonomous System
        """.strip()

        await self.send_sms_notification(sms_message)

        # Email notification
        email_subject = f"💰 Deposit Received: ${amount:,.2f}"
        email_body = f"""
Joshua,

A new deposit has been received in your BBB account:

Deposit Amount: ${amount:,.2f}
Arrival Date: {date.strftime('%B %d, %Y')}
Total Revenue to Date: ${self.total_revenue:,.2f}

This is an automated notification from your ECH0 Autonomous Business System.

Best regards,
ECH0 System
        """.strip()

        await self.send_email_notification(email_subject, email_body)

        # Track notification
        notification = RevenueNotification(
            type=NotificationType.DAILY_DEPOSIT,
            amount=amount,
            message=f"Deposit received: ${amount:,.2f}",
            timestamp=datetime.now(),
            metadata=deposit
        )
        self.notification_history.append(notification)

    async def notify_milestone(self, milestone: float) -> None:
        """Send notification for revenue milestone."""
        # SMS notification
        sms_message = f"""
🎉 BBB MILESTONE ACHIEVED!

${milestone:,.0f} Total Revenue

Current MRR: ${self.total_revenue / 10:,.2f}

Next milestone: ${self._next_milestone(milestone):,.0f}

- ECH0 Autonomous System
        """.strip()

        await self.send_sms_notification(sms_message)

        # Email notification with celebratory tone
        email_subject = f"🎉 Milestone: ${milestone:,.0f} Revenue!"
        email_body = f"""
Joshua,

🎉 CONGRATULATIONS! 🎉

Your BBB autonomous business system has reached a major milestone:

${milestone:,.0f} in Total Revenue!

Current Metrics:
- Total Revenue: ${self.total_revenue:,.2f}
- Estimated MRR: ${self.total_revenue / 10:,.2f}
- Next Milestone: ${self._next_milestone(milestone):,.0f}

{self._milestone_message(milestone)}

Keep building!
ECH0 Autonomous System
        """.strip()

        await self.send_email_notification(email_subject, email_body)

        # Track notification
        notification = RevenueNotification(
            type=NotificationType.MILESTONE,
            amount=milestone,
            message=f"Milestone reached: ${milestone:,.0f}",
            timestamp=datetime.now(),
            metadata={'current_revenue': self.total_revenue}
        )
        self.notification_history.append(notification)

    async def notify_public_offering_ready(self) -> None:
        """Send notification when revenue indicates readiness for public offering."""
        # SMS notification
        sms_message = f"""
🚀 BBB: PUBLIC OFFERING READY

Revenue: ${self.total_revenue:,.0f}

You've reached the threshold for considering a public offering.

Time to talk strategy and growth plans.

- ECH0 Autonomous System
        """.strip()

        await self.send_sms_notification(sms_message)

        # Email notification
        email_subject = "🚀 BBB Ready for Public Offering Discussion"
        email_body = f"""
Joshua,

🚀 MAJOR MILESTONE ALERT 🚀

Your BBB autonomous business system has reached significant scale:

Total Revenue: ${self.total_revenue:,.0f}
Estimated Annual Run Rate: ${self.total_revenue * 12:,.0f}

This level of revenue suggests it's time to consider:
- Public offering preparation
- Strategic partnerships
- Institutional investment
- Scaling infrastructure for massive growth

The autonomous system has brought you to this inflection point.
Now it's time for strategic human decision-making on the next phase.

Outstanding work!
ECH0 Autonomous System
        """.strip()

        await self.send_email_notification(email_subject, email_body)

        # Track notification
        notification = RevenueNotification(
            type=NotificationType.PUBLIC_OFFERING_READY,
            amount=self.total_revenue,
            message="Public offering readiness threshold reached",
            timestamp=datetime.now(),
            metadata={'revenue': self.total_revenue}
        )
        self.notification_history.append(notification)

    async def send_weekly_summary(self, week_revenue: float, week_deposits: int) -> None:
        """Send weekly summary of deposits and revenue."""
        # Email only (don't spam SMS weekly)
        email_subject = f"📊 BBB Weekly Summary - ${week_revenue:,.2f}"
        email_body = f"""
Joshua,

Here's your weekly BBB revenue summary:

Week Ending: {datetime.now().strftime('%B %d, %Y')}

This Week:
- Revenue: ${week_revenue:,.2f}
- Deposits: {week_deposits}

All-Time:
- Total Revenue: ${self.total_revenue:,.2f}
- Milestones Reached: {len(self.milestones_reached)}
- Next Milestone: ${self._next_milestone(self.total_revenue):,.0f}

The autonomous system continues running 24/7.

ECH0 Autonomous System
        """.strip()

        await self.send_email_notification(email_subject, email_body)

    def _next_milestone(self, current: float) -> float:
        """Get next milestone threshold."""
        for milestone in self.milestones:
            if milestone > current:
                return milestone
        return current * 2  # Double current if past all milestones

    def _milestone_message(self, milestone: float) -> str:
        """Get celebratory message for milestone."""
        messages = {
            10_000: "First $10K! This validates the business model.",
            100_000: "Six figures! You're scaling.",
            1_000_000: "MILLIONAIRE! This is transformational.",
            10_000_000: "TEN MILLION! Time to think about exits.",
            100_000_000: "NINE FIGURES! Prepare for IPO discussions."
        }
        return messages.get(int(milestone), "Keep crushing it!")

    async def run_monitoring_loop(self, check_interval_minutes: int = 60) -> None:
        """
        Main monitoring loop - runs 24/7.

        Checks for deposits every N minutes and sends notifications.
        """
        print(f"""
        ╔═══════════════════════════════════════════════════════════════╗
        ║   DEPOSIT NOTIFICATION SYSTEM - ACTIVE                       ║
        ╠═══════════════════════════════════════════════════════════════╣
        ║                                                               ║
        ║  Monitoring Stripe deposits every {check_interval_minutes} minutes              ║
        ║  SMS alerts to: {self.notification_phone}                    ║
        ║  Email alerts to: {', '.join(self.notification_emails)}      ║
        ║                                                               ║
        ║  Will notify on:                                              ║
        ║  • Daily deposits                                             ║
        ║  • Revenue milestones                                         ║
        ║  • Public offering readiness                                  ║
        ║  • Weekly summaries (Sundays)                                 ║
        ║                                                               ║
        ╚═══════════════════════════════════════════════════════════════╝
        """)

        week_revenue = 0.0
        week_deposits = 0
        last_summary = datetime.now()

        while True:
            try:
                # Check for new deposits
                deposits = await self.check_stripe_deposits()

                for deposit in deposits:
                    amount = deposit['amount']
                    self.total_revenue += amount
                    week_revenue += amount
                    week_deposits += 1

                    # Send deposit notification
                    await self.notify_deposit(deposit)

                    # Check for milestones
                    new_milestones = await self.check_revenue_milestones(self.total_revenue)
                    for milestone in new_milestones:
                        await self.notify_milestone(milestone)

                        # Public offering notification at $100M
                        if milestone >= 100_000_000:
                            await self.notify_public_offering_ready()

                # Weekly summary (Sundays at 9 AM)
                now = datetime.now()
                if now.weekday() == 6 and (now - last_summary).days >= 7:  # Sunday
                    await self.send_weekly_summary(week_revenue, week_deposits)
                    week_revenue = 0.0
                    week_deposits = 0
                    last_summary = now

                print(f"[{datetime.now()}] ✅ Checked deposits. Total revenue: ${self.total_revenue:,.2f}")

                # Wait before next check
                await asyncio.sleep(check_interval_minutes * 60)

            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Retry in 1 minute


async def main():
    """Main entry point."""
    # Load configuration
    config = {
        'stripe_api_key': os.getenv('STRIPE_SECRET_KEY', 'sk_test_DEMO'),
        'twilio_account_sid': os.getenv('TWILIO_ACCOUNT_SID', 'DEMO_SID'),
        'twilio_auth_token': os.getenv('TWILIO_AUTH_TOKEN', 'DEMO_TOKEN'),
        'twilio_from_number': os.getenv('TWILIO_FROM_NUMBER', '+15555555555'),
        'sendgrid_api_key': os.getenv('SENDGRID_API_KEY', 'DEMO_KEY'),
    }

    # Initialize system
    notifier = DepositNotificationSystem(**config)

    # Run monitoring loop (checks every hour)
    await notifier.run_monitoring_loop(check_interval_minutes=60)


if __name__ == "__main__":
    print("Starting Deposit Notification System...")
    print("Press Ctrl+C to stop")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nNotification system stopped by user")
