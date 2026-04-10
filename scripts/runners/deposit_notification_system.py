#!/usr/bin/env python3
"""
Deposit Notification System - Real World Revenue Alerts
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Monitors real Stripe deposits and database revenue metrics.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

import stripe
from twilio.rest import Client
from sqlalchemy import func

from blank_business_builder.database import get_db_engine, get_session, Business, MetricsHistory
from blank_business_builder.config import settings
from blank_business_builder.integrations import IntegrationFactory

class NotificationType(Enum):
    """Types of revenue notifications."""
    DAILY_DEPOSIT = "daily_deposit"
    MILESTONE = "milestone"
    PUBLIC_OFFERING_READY = "public_offering_ready"

class DepositNotificationSystem:
    def __init__(self):
        # Database
        self.engine = get_db_engine(settings.DATABASE_URL)

        # Stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        # Services
        self.email_service = IntegrationFactory.get_sendgrid_service()
        self.twilio_client = None
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            self.twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        self.notification_phone = "+17252242617" # User provided
        self.notification_emails = ["inventor@aios.is", "echo@aios.is"]

        # State
        self.last_deposit_check = datetime.now()
        self.milestones_reached = set()
        self.milestones = [
            10000, 50000, 100000, 250000, 500000, 1000000,
            5000000, 10000000, 50000000, 100000000
        ]

    def get_total_revenue(self) -> float:
        """Get total revenue across all businesses from DB."""
        db = get_session(self.engine)
        total = db.query(func.sum(Business.total_revenue)).scalar() or 0.0
        db.close()
        return float(total)

    async def check_stripe_deposits(self) -> List[Dict[str, Any]]:
        """Check Stripe for new payouts."""
        if not settings.STRIPE_SECRET_KEY or "DEMO" in settings.STRIPE_SECRET_KEY:
            print("⚠️  Stripe Key Missing or Demo. Skipping real deposit check.")
            return []

        try:
            payouts = stripe.Payout.list(
                created={'gte': int(self.last_deposit_check.timestamp())},
                limit=10
            )

            new_deposits = []
            for payout in payouts.auto_paging_iter():
                if payout.status == "paid":
                    new_deposits.append({
                        'amount': payout.amount / 100,
                        'date': datetime.fromtimestamp(payout.arrival_date)
                    })

            self.last_deposit_check = datetime.now()
            return new_deposits
        except Exception as e:
            print(f"❌ Stripe Error: {e}")
            return []

    async def send_sms(self, message: str):
        if self.twilio_client:
            try:
                self.twilio_client.messages.create(
                    body=message,
                    from_=settings.TWILIO_FROM_NUMBER,
                    to=self.notification_phone
                )
                print(f"✅ SMS Sent: {message[:30]}...")
            except Exception as e:
                print(f"❌ SMS Failed: {e}")
        else:
            print(f"⚠️  Twilio not configured. SMS would be: {message}")

    async def send_email(self, subject: str, body: str):
        for email in self.notification_emails:
            try:
                self.email_service.send_email(
                    to_email=email,
                    subject=subject,
                    html_content=body,
                    use_queue=False
                )
                print(f"✅ Email Sent to {email}")
            except Exception as e:
                print(f"❌ Email Failed: {e}")

    async def run_monitoring_loop(self, interval_seconds=3600):
        print("💰 Deposit Notification System Active")
        print(f"Checking every {interval_seconds} seconds")

        while True:
            try:
                # 1. Check Deposits
                deposits = await self.check_stripe_deposits()
                total_rev = self.get_total_revenue()

                for deposit in deposits:
                    msg = f"💰 Deposit: ${deposit['amount']:,.2f}\nTotal Rev: ${total_rev:,.2f}"
                    await self.send_sms(msg)
                    await self.send_email("💰 New Deposit Received", msg)

                # 2. Check Milestones
                for m in self.milestones:
                    if total_rev >= m and m not in self.milestones_reached:
                        self.milestones_reached.add(m)
                        msg = f"🎉 Milestone Reached: ${m:,.0f} Revenue!"
                        await self.send_sms(msg)
                        await self.send_email(f"🎉 Milestone: ${m:,.0f}", msg)

                        if m >= 100_000_000:
                            await self.send_email("🚀 PUBLIC OFFERING READY", "Revenue > $100M. Initiate IPO protocols.")

                await asyncio.sleep(interval_seconds)

            except Exception as e:
                print(f"❌ Monitor Error: {e}")
                await asyncio.sleep(60)

async def main():
    monitor = DepositNotificationSystem()
    await monitor.run_monitoring_loop(interval_seconds=60) # Check every minute for responsiveness

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMonitor stopped.")
