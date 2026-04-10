"""
AUTONOMOUS BUSINESS RUNNER - REAL WORLD ENGINE
Main engine for autonomous business operation using persistent database state.
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

import argparse
import time
import json
import os
import sys
from datetime import datetime, timedelta
import asyncio

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from sqlalchemy.orm import Session
from sqlalchemy import func

from blank_business_builder.database import get_db_engine, get_session, Business, MetricsHistory, AgentTask, Subscription
from blank_business_builder.config import settings
from blank_business_builder.integrations import IntegrationFactory

# Real-world constraints
MIN_PRICE = 5.0
MAX_CONVERSION_RATE = 0.15 # 15%

class AutonomousBusinessRunner:
    def __init__(self, mode='production'):
        self.mode = mode
        self.engine = get_db_engine(settings.DATABASE_URL)
        self.log_dir = "./FlowState/logs"
        os.makedirs(self.log_dir, exist_ok=True)
        self.stripe_service = IntegrationFactory.get_stripe_service() if hasattr(IntegrationFactory, 'get_stripe_service') else None

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        with open(f"{self.log_dir}/autonomous_business_real.log", "a") as f:
            f.write(f"[{timestamp}] {message}\n")

    def execute_daily_operations(self, db: Session, business: Business):
        """
        Execute daily operations for a single business.
        Updates DB state based on REAL metrics and business rules.
        """
        self.log(f"Processing Business: {business.business_name} ({business.id})")

        # 1. Check Real Marketing Activity
        # Count completed marketing tasks in the last 24h
        marketing_tasks = db.query(AgentTask).filter(
            AgentTask.business_id == business.id,
            AgentTask.agent_role == 'marketer',
            AgentTask.status == 'completed',
            AgentTask.completed_at >= datetime.utcnow() - timedelta(days=1)
        ).count()

        # 2. Check Real Leads
        # In a real system, leads come from landing page signups (User table) or CRM.
        # For now, we check if we have any *new* potential customers in the User table linked to this business context?
        # Since `Business` doesn't link to `User` as customers directly (only owner),
        # we rely on `business.total_leads` which should be updated by the API/Webhooks.
        # If no external update happened, new_leads is 0.
        # This is REAL WORLD behavior: No marketing/traffic = No leads.
        new_leads = 0

        # 3. Check Real Subscriptions (Stripe)
        # We query the `Subscription` table which should be synced with Stripe via webhooks.
        active_subs = db.query(Subscription).filter(
            Subscription.status == 'active'
            # In a multi-tenant system, Subscription should link to Business, but currently links to User.
            # Assuming Business Owner's subscriptions for now, or we'd need to link Sub -> Business.
            # For this "Business Runner", we track the *Business's* customers.
            # The current model `Subscription` is for the *User* paying for the platform, not the Business's customers.
            # We'll use `business.total_customers` as the source of truth, updated by external sales logic.
        ).count()

        # If we have a Stripe integration for the *Business's* customers (Connect), we'd query that.
        # Without it, we rely on what's in the DB.
        current_customers = business.total_customers or 0

        # 4. Revenue (Synced from Stripe via Deposit System)
        # We do NOT calculate revenue here. We read it.
        daily_revenue = 0.0 # Revenue is an accumulation, not a daily rate unless we calculate daily run rate.
        # We can calculate "Estimated Daily Revenue" based on active customers * ARPU if we want a metric.
        # But `total_revenue` is historical.

        # 5. Record History
        # We record the snapshot of the business state.
        history = MetricsHistory(
            business_id=business.id,
            revenue=business.total_revenue, # Current total
            customers=current_customers,
            leads=business.total_leads,
            conversion_rate=business.conversion_rate,
            tasks_completed=marketing_tasks
        )
        db.add(history)

        self.log(f"  -> State: {current_customers} Cust, ${business.total_revenue} Total Rev")

    def run_production(self):
        self.log(f"🚀 Starting REAL-WORLD Business Runner")
        self.log(f"Database: {settings.DATABASE_URL}")

        while True:
            try:
                db = get_session(self.engine)
                # Fetch active businesses
                businesses = db.query(Business).filter(Business.status == 'active').all()

                if not businesses:
                    self.log("No active businesses found. Sleeping...")
                else:
                    self.log(f"Found {len(businesses)} active businesses.")
                    for biz in businesses:
                        self.execute_daily_operations(db, biz)

                    db.commit()
                    self.log("✅ Daily operations cycle complete. Updates committed.")

                db.close()

                # Sleep for a significant time in production (e.g. 1 hour)
                # For responsiveness in this environment, we use 60s.
                time.sleep(60)

            except Exception as e:
                self.log(f"❌ Error in runner loop: {e}")
                time.sleep(60)

def main():
    parser = argparse.ArgumentParser(description='Autonomous Business Runner - Real World')
    parser.add_argument('--mode', type=str, default='production', help='Execution mode')
    args = parser.parse_args()

    runner = AutonomousBusinessRunner(mode=args.mode)
    try:
        runner.run_production()
    except KeyboardInterrupt:
        print("\nRunner stopped by user.")

if __name__ == "__main__":
    main()
