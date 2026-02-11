#!/usr/bin/env python3
"""
FIVERR AUTONOMOUS WATCHDOG - Standalone Service
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

This watchdog runs 24/7 monitoring Fiverr for:
- New messages (inbox scanning)
- Active orders (order management)
- Human-like randomized check intervals
- Automatic session recovery

USAGE:
  python fiverr_watchdog_autonomous.py

REQUIREMENTS:
  - Chrome profile with active Fiverr login
  - Set FIVERR_CHROME_PROFILE_PATH environment variable
  - pip install selenium webdriver-manager
"""

import os
import sys
import time
import random
import signal
import json
from datetime import datetime
from pathlib import Path

try:
    from fiverr_autonomous_manager import FiverrAutonomousManager
except ImportError:
    print("[FATAL] fiverr_autonomous_manager.py not found in current directory")
    sys.exit(1)


class FiverrWatchdog:
    """
    Autonomous 24/7 watchdog for Fiverr business management.
    Mimics human behavior patterns to avoid detection.
    """

    def __init__(self, log_path="/Users/noone/.ech0/fiverr_watchdog.log"):
        self.log_path = log_path
        self.running = True
        self.agent = None
        self.stats = {
            "started_at": datetime.now().isoformat(),
            "total_checks": 0,
            "messages_found": 0,
            "orders_found": 0,
            "errors": 0,
            "last_check": None
        }

        # Create log directory
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.log("WATCHDOG", "Initializing Fiverr Autonomous Watchdog...")

    def log(self, category: str, message: str):
        """Log message to both console and file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{category}] {message}"

        print(log_entry)

        with open(self.log_path, 'a') as f:
            f.write(log_entry + "\n")

    def process_orders(self, orders):
        """Process a list of active orders."""
        self.log("ORDERS", f"Processing {len(orders)} active orders...")

        for order in orders:
            order_id = order.get("id", "unknown")
            summary = order.get("text_summary", "No details")
            self.log("ORDER_PROC", f"Processing Order #{order_id}: {summary}")

            # Placeholder for future logic
            # e.g. if "late" in summary.lower(): self.alert_late_order(order)

        self.log("ORDERS", "Order processing cycle complete.")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.log("WATCHDOG", f"Received signal {signum}, initiating graceful shutdown...")
        self.running = False

    def human_sleep_interval(self) -> int:
        """
        Return a human-like sleep interval (in seconds).
        Mimics biological irregularity:
        - Most checks: 5-15 minutes
        - Occasional longer breaks: 20-45 minutes
        - Rare extended breaks: 1-2 hours
        """
        rand = random.random()

        if rand < 0.70:  # 70% of the time: quick checks
            return random.randint(300, 900)  # 5-15 minutes
        elif rand < 0.90:  # 20% of the time: medium breaks
            return random.randint(1200, 2700)  # 20-45 minutes
        else:  # 10% of the time: extended breaks
            return random.randint(3600, 7200)  # 1-2 hours

    def initialize_agent(self) -> bool:
        """Initialize or reinitialize the Fiverr agent."""
        try:
            self.log("AGENT", "Initializing Fiverr Autonomous Manager...")
            self.agent = FiverrAutonomousManager()
            self.log("AGENT", "Agent initialized successfully")
            return True
        except Exception as e:
            self.log("ERROR", f"Agent initialization failed: {e}")
            self.stats["errors"] += 1
            return False

    def check_fiverr_activity(self) -> bool:
        """
        Perform a full Fiverr check cycle:
        1. Connect to dashboard
        2. Scan inbox for messages
        3. Check active orders
        """
        try:
            self.stats["total_checks"] += 1
            self.stats["last_check"] = datetime.now().isoformat()

            # Connect to dashboard
            if not self.agent.connect_to_dashboard():
                self.log("WARN", "Failed to connect to dashboard, session may have expired")
                return False

            # Scan inbox
            time.sleep(random.uniform(2, 5))  # Human-like pause
            num_messages = self.agent.scan_inbox()

            if num_messages > 0:
                self.stats["messages_found"] += num_messages
                self.log("INBOX", f"Found {num_messages} unread message(s)")
                # TODO: Integrate with LLM for auto-response
            else:
                self.log("INBOX", "No new messages")

            # Check orders
            time.sleep(random.uniform(3, 7))  # Human-like pause
            active_orders = self.agent.get_active_order_details()
            num_orders = len(active_orders)

            if num_orders > 0:
                self.stats["orders_found"] += num_orders
                self.log("ORDERS", f"Found {num_orders} active order(s)")
                self.process_orders(active_orders)
            else:
                self.log("ORDERS", "No active orders")

            return True

        except Exception as e:
            self.log("ERROR", f"Check cycle failed: {e}")
            self.stats["errors"] += 1
            return False

    def save_stats(self):
        """Save statistics to JSON file."""
        stats_path = "/Users/noone/.ech0/fiverr_watchdog_stats.json"
        try:
            with open(stats_path, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            self.log("WARN", f"Could not save stats: {e}")

    def run(self):
        """
        Main watchdog loop.
        Runs indefinitely until interrupted.
        """
        self.log("WATCHDOG", "╔════════════════════════════════════════════════════╗")
        self.log("WATCHDOG", "║  FIVERR AUTONOMOUS WATCHDOG - ENGAGED             ║")
        self.log("WATCHDOG", "║  24/7 Monitoring Active                            ║")
        self.log("WATCHDOG", "╚════════════════════════════════════════════════════╝")

        # Initialize agent
        if not self.initialize_agent():
            self.log("FATAL", "Could not initialize agent. Exiting.")
            return

        consecutive_failures = 0
        max_consecutive_failures = 3

        while self.running:
            try:
                # Perform check cycle
                success = self.check_fiverr_activity()

                if success:
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    self.log("WARN", f"Check failed. Consecutive failures: {consecutive_failures}")

                # If too many consecutive failures, reinitialize agent
                if consecutive_failures >= max_consecutive_failures:
                    self.log("RECOVERY", "Too many failures, reinitializing agent...")
                    if self.agent:
                        self.agent.shutdown()
                    time.sleep(30)  # Wait before reinit
                    if self.initialize_agent():
                        consecutive_failures = 0
                    else:
                        self.log("ERROR", "Reinitialization failed, waiting before retry...")
                        time.sleep(300)  # Wait 5 minutes

                # Save stats periodically
                if self.stats["total_checks"] % 10 == 0:
                    self.save_stats()

                # Human-like sleep interval
                if self.running:
                    sleep_duration = self.human_sleep_interval()
                    self.log("WATCHDOG", f"Next check in {sleep_duration // 60} minutes ({sleep_duration}s)")
                    time.sleep(sleep_duration)

            except KeyboardInterrupt:
                self.log("WATCHDOG", "Keyboard interrupt received")
                break
            except Exception as e:
                self.log("ERROR", f"Unexpected error in main loop: {e}")
                self.stats["errors"] += 1
                time.sleep(60)  # Wait 1 minute before retry

        # Shutdown
        self.log("WATCHDOG", "Shutting down watchdog...")
        if self.agent:
            self.agent.shutdown()

        self.save_stats()
        self.log("WATCHDOG", f"Final stats: {self.stats}")
        self.log("WATCHDOG", "Watchdog shutdown complete")


def main():
    """Entry point for standalone watchdog."""
    print("\n" + "="*60)
    print("  FIVERR AUTONOMOUS WATCHDOG v1.0")
    print("  Copyright (c) 2025 Joshua Hendricks Cole")
    print("  Corporation of Light - PATENT PENDING")
    print("="*60 + "\n")

    # Verify environment
    if not os.getenv("FIVERR_CHROME_PROFILE_PATH"):
        print("[WARN] FIVERR_CHROME_PROFILE_PATH not set")
        print("[INFO] Defaulting to system detection (may fail)")

    # Create and run watchdog
    watchdog = FiverrWatchdog()
    watchdog.run()


if __name__ == "__main__":
    main()
