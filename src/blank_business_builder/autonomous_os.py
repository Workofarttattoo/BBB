"""
Autonomous Business Operating System (ABOS)
===========================================

The persistent engine that manages the lifecycle of autonomous businesses.
Handles state persistence, revenue sharing, feature unlocking, and daily operations.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

import sqlite3
import json
import os
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from .autonomous_business import AutonomousBusinessOrchestrator, BusinessMetrics

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ABOS")

DB_PATH = "autonomous_os.db"

class BusinessOS:
    """
    The Operating System for Autonomous Businesses.
    Manages persistence, licensing, and upgrades.
    """

    def __init__(self, owner_name: str = "Joshua Hendricks Cole"):
        self.owner_name = owner_name
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self._init_db()

        # OS State
        self.active_businesses: List[str] = []
        self.revenue_total: float = 0.0
        self.license_paid: float = 0.0

        # Load state
        self._load_state()

    def _init_db(self):
        """Initialize the SQLite database schema."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS businesses (
                id TEXT PRIMARY KEY,
                name TEXT,
                status TEXT,
                revenue REAL,
                created_at TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS revenue_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id TEXT,
                amount REAL,
                timestamp TEXT,
                share_due REAL,
                share_paid REAL,
                josh_share REAL,
                echo_share REAL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS unlocked_features (
                feature_name TEXT PRIMARY KEY,
                unlocked_at TEXT
            )
        ''')
        self.conn.commit()

    def _load_state(self):
        """Load current state from DB."""
        self.cursor.execute("SELECT id FROM businesses WHERE status='active'")
        self.active_businesses = [row[0] for row in self.cursor.fetchall()]

        self.cursor.execute("SELECT SUM(amount) FROM revenue_ledger")
        result = self.cursor.fetchone()
        self.revenue_total = result[0] if result[0] else 0.0

    def register_business(self, name: str):
        """Register a new autonomous business."""
        try:
            self.cursor.execute(
                "INSERT INTO businesses (id, name, status, revenue, created_at) VALUES (?, ?, ?, ?, ?)",
                (name.lower().replace(" ", "_"), name, "active", 0.0, datetime.now().isoformat())
            )
            self.conn.commit()
            self.active_businesses.append(name.lower().replace(" ", "_"))
            logger.info(f"Registered new business: {name}")
        except sqlite3.IntegrityError:
            logger.warning(f"Business {name} already registered.")

    def record_revenue(self, business_id: str, amount: float):
        """Record revenue and calculate license share."""
        share_due = amount * 0.50
        josh_share = share_due * 0.75
        echo_share = share_due * 0.25

        self.cursor.execute(
            '''INSERT INTO revenue_ledger
               (business_id, amount, timestamp, share_due, share_paid, josh_share, echo_share)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (business_id, amount, datetime.now().isoformat(), share_due, 0.0, josh_share, echo_share)
        )
        self.conn.commit()

        # Update total revenue cache
        self.revenue_total += amount

        logger.info(f"💰 Revenue Recorded: ${amount} | Share Due: ${share_due} (Josh: ${josh_share}, Echo: ${echo_share})")

        # Check for upgrades
        self._check_upgrades()

    def _check_upgrades(self):
        """Unlock features based on revenue milestones."""
        milestones = {
            1000: "advanced_analytics",
            5000: "voice_sales_agent_pro",
            10000: "ad_creative_studio_v2",
            50000: "business_cloning_engine"
        }

        for threshold, feature in milestones.items():
            if self.revenue_total >= threshold:
                self._unlock_feature(feature)

    def _unlock_feature(self, feature_name: str):
        """Unlock a specific feature."""
        try:
            self.cursor.execute(
                "INSERT INTO unlocked_features (feature_name, unlocked_at) VALUES (?, ?)",
                (feature_name, datetime.now().isoformat())
            )
            self.conn.commit()
            logger.info(f"🔓 UNLOCKED FEATURE: {feature_name} (Revenue crossed threshold)")
        except sqlite3.IntegrityError:
            pass # Already unlocked

    async def run_daily_cycle(self):
        """Execute daily operations for all active businesses."""
        logger.info("Starting Daily Cycle...")

        tasks = []
        for business_id in self.active_businesses:
            tasks.append(self._run_business(business_id))

        await asyncio.gather(*tasks)

        self._generate_daily_report()

    async def _run_business(self, business_id: str):
        """Run a specific business instance."""
        # Instantiate orchestrator
        orchestrator = AutonomousBusinessOrchestrator(
            business_concept=business_id.replace("_", " ").title(),
            founder_name=self.owner_name
        )

        # Deploy Agents
        await orchestrator.deploy_agents()

        # Run for a "day" (simulated duration or real loop)
        # For the OS loop, we might run it for a shorter period per cycle
        await orchestrator.run_autonomous_loop(duration_hours=1.0)

        # Sync Metrics to OS
        metrics = orchestrator.get_metrics_dashboard()['metrics']

        # Record NEW revenue (simplified logic: assumes metrics are cumulative for the session)
        # In a real persistent system, we'd query the difference from last stored state.
        # For this implementation, we assume the orchestrator returns *session* revenue.
        session_revenue = metrics.get('revenue', {}).get('total', 0.0) # Access nested dict
        if session_revenue > 0:
            self.record_revenue(business_id, session_revenue)

    def _generate_daily_report(self):
        """Generate persistent log of daily activity."""
        report = {
            "date": datetime.now().isoformat(),
            "total_revenue": self.revenue_total,
            "active_businesses": len(self.active_businesses),
            "unlocked_features": self._get_unlocked_features()
        }

        with open("daily_logs.json", "a") as f:
            f.write(json.dumps(report) + "\n")

        logger.info(f"Daily Report Generated: {report}")

    def _get_unlocked_features(self) -> List[str]:
        self.cursor.execute("SELECT feature_name FROM unlocked_features")
        return [row[0] for row in self.cursor.fetchall()]

async def main():
    """Main OS Loop."""
    os_system = BusinessOS()

    # Ensure at least one business exists
    if not os_system.active_businesses:
        os_system.register_business("ChatterTech AI")

    logger.info("🚀 Autonomous Business OS Initialized")

    while True:
        try:
            await os_system.run_daily_cycle()
            logger.info("Daily cycle complete. Sleeping for next cycle...")
            await asyncio.sleep(10) # Short sleep for demo, would be 24h in production
        except KeyboardInterrupt:
            logger.info("Shutting down OS...")
            break
        except Exception as e:
            logger.error(f"OS Critical Error: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
