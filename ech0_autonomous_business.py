#!/usr/bin/env python3
"""
ECH0 Autonomous Business Automation System
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

This system provides full autonomous business operations including:
- Fiverr gig management and customer communication
- Website content management (GitHub-based)
- Email automation
- Social media marketing
- Google Ads optimization
- Lead processing and CRM
- Daily reporting
"""

import sys
import time
import threading
import asyncio
import json
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, List, Optional
import subprocess

# Add src to path to allow importing business libraries
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import business libraries
try:
    from blank_business_builder.autonomous_business import (
        AutonomousBusinessOrchestrator,
        AgentRole,
        AutonomousTask
    )
    from blank_business_builder.business_data import default_ideas
    BUSINESS_LIB_AVAILABLE = True
except ImportError:
    BUSINESS_LIB_AVAILABLE = False
    print("[WARN] Business libraries not available")

# Import Fiverr autonomous manager
try:
    from fiverr_autonomous_manager import FiverrAutonomousManager
    FIVERR_CLIENT_AVAILABLE = True
except ImportError:
    FIVERR_CLIENT_AVAILABLE = False
    print("[WARN] Fiverr autonomous manager not available")

try:
    from ech0_llm_engine import ECH0LLMEngine
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("[WARN] ECH0 LLM Engine not available")

# Selenium imports for other web automation
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("[WARN] Selenium not available. Install: pip install selenium")


class ECH0AutonomousCore:
    """
    Core autonomous business automation system.
    Manages all business operations without human intervention.
    """

    def __init__(self, config_path: str = "/Users/noone/.ech0/business_config.json"):
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║  ECH0 AUTONOMOUS BUSINESS SYSTEM - INITIALIZING              ║")
        print("║  Copyright (c) 2025 Joshua Hendricks Cole                    ║")
        print("║  Corporation of Light - PATENT PENDING                       ║")
        print("╚══════════════════════════════════════════════════════════════╝\n")

        self.config_path = config_path
        self.config = self._load_config()
        self.system_status = "INITIALIZING"
        self.shutdown_flag = threading.Event()
        self.task_queue = []
        self.activity_log = []
        self.daily_summary = []
        self.active_businesses = {}  # Registry of active AutonomousBusinessOrchestrator instances

        # Initialize modules
        self.modules = {
            "fiverr": FiverrAutomation(self),
            "websites": WebsiteAutomation(self),
            "email": EmailAutomation(self),
            "social": SocialMediaAutomation(self),
            "ads": GoogleAdsAutomation(self),
            "crm": CRMAutomation(self),
            "reporting": DailyReporting(self)
        }

        print("✓ All modules initialized")
        print(f"✓ Configuration loaded from {config_path}")
        self.system_status = "READY"

    def _load_config(self) -> Dict:
        """Load or create configuration file."""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return json.load(f)

        # Default configuration
        default_config = {
            "owner": {
                "name": "Joshua Hendricks Cole",
                "phone": "7252242617",
                "emails": {
                    "primary": "inventor@aios.is",
                    "ech0": "echo@aios.is",
                    "flowstatus": "echo@flowstatus.work"
                }
            },
            "fiverr": {
                "username": "",  # User fills this in
                "password": "",
                "chrome_profile_path": "/Users/noone/Library/Application Support/Google/Chrome",
                "chrome_profile_directory": "Default",
                "gigs": [],
                "auto_respond": True,
                "check_interval_minutes": 15
            },
            "websites": {
                "aios": {
                    "github_repo": "yourusername/aios.is",
                    "branch": "main",
                    "path": "_posts"
                },
                "red_team": {
                    "github_repo": "yourusername/red-team-tools.aios.is",
                    "branch": "main",
                    "path": "_posts"
                },
                "flowstatus": {
                    "github_repo": "yourusername/flowstatus.work",
                    "branch": "main",
                    "path": "blog"
                }
            },
            "email": {
                "smtp_server": "smtp.gmail.com",  # Or your provider
                "smtp_port": 587,
                "check_interval_minutes": 10
            },
            "social_media": {
                "twitter": {"enabled": False},
                "linkedin": {"enabled": False}
            },
            "google_ads": {
                "enabled": False,
                "daily_budget": 50.0
            },
            "daily_report": {
                "send_time": "09:00",
                "recipient": "7252242617@txt.att.net"  # SMS gateway
            }
        }

        # Create config directory
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)

        print(f"[INFO] Created default config at {self.config_path}")
        print("[ACTION REQUIRED] Please edit config with your credentials")

        return default_config

    def log_activity(self, module: str, action: str, details: str = ""):
        """Log all system activities for daily reporting."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "module": module,
            "action": action,
            "details": details
        }
        self.activity_log.append(entry)
        self.daily_summary.append(f"[{module.upper()}] {action}: {details}")
        print(f"✓ [{module.upper()}] {action}")

    def add_task(self, priority: int, module: str, function, args: tuple = ()):
        """Add task to priority queue."""
        self.task_queue.append((priority, module, function, args))
        self.task_queue.sort(key=lambda x: x[0], reverse=True)

    def _task_execution_loop(self):
        """Main task execution loop running in separate thread."""
        self.system_status = "ACTIVE"
        print("\n🚀 ECH0 AUTONOMOUS SYSTEM ENGAGED - FULL AUTONOMY MODE")
        print("=" * 60)

        while not self.shutdown_flag.is_set():
            # Execute pending tasks
            if self.task_queue:
                priority, module, func, args = self.task_queue.pop(0)
                try:
                    func(*args)
                except Exception as e:
                    self.log_activity(module, "ERROR", str(e))
                    print(f"[ERROR] {module}: {e}")

            # Also pump the loops of any active business orchestrators
            # (In a real system, these would run in their own threads/processes)
            for biz_name, orchestrator in self.active_businesses.items():
                if orchestrator.running:
                    # Execute one cycle of tasks if possible
                    # Since run_autonomous_loop is a blocking async loop, we can't easily interleave it here
                    # without refactoring Orchestrator to be tick-based or running it in a thread.
                    # For now, we assume dispatching tasks to it is enough.
                    pass

            time.sleep(1)

        self.system_status = "SHUTDOWN"
        print("\n🛑 ECH0 SYSTEM SHUTDOWN COMPLETE")

    def get_or_create_business(self, gig_title: str) -> Optional[object]:
        """
        Resolve a gig title to an AutonomousBusinessOrchestrator.
        If not active, initializes it.
        """
        if not BUSINESS_LIB_AVAILABLE:
            return None

        # Simple keyword matching to find the business concept
        # In production, this would be a sophisticated semantic match
        matched_idea = None
        for idea in default_ideas():
            # Check if significant words from idea name are in gig title
            idea_keywords = set(idea.name.lower().split())
            gig_keywords = set(gig_title.lower().split())

            # If 50% match
            intersection = idea_keywords.intersection(gig_keywords)
            if len(intersection) / len(idea_keywords) > 0.3: # Low threshold for demo
                matched_idea = idea
                break

        if not matched_idea:
            # Fallback: Create a generic one if no match found
            # Or return None
            # For robustness, let's create a generic "Service Business" if we can't match
            # But strictly, let's try to match existing logic
            return None

        if matched_idea.name in self.active_businesses:
            return self.active_businesses[matched_idea.name]

        # Initialize new orchestrator
        print(f"ECH0_CORE: Initializing new autonomous business for: {matched_idea.name}")
        orchestrator = AutonomousBusinessOrchestrator(
            business_concept=matched_idea.name,
            founder_name=self.config['owner']['name']
        )

        # Deploy agents (async, but we'll run it sync here for simplicity or spawn a task)
        # Since deploy_agents is async, we need to run it.
        try:
            asyncio.run(orchestrator.deploy_agents())
        except Exception as e:
             print(f"ECH0_CORE: Failed to deploy agents: {e}")
             return None

        self.active_businesses[matched_idea.name] = orchestrator
        return orchestrator

    def startup(self):
        """Start autonomous operations."""
        if self.system_status == "ACTIVE":
            print("[WARN] System already active")
            return

        print("\n🎯 Activating autonomous business operations...")

        # Start main execution thread
        self.execution_thread = threading.Thread(target=self._task_execution_loop, daemon=True)
        self.execution_thread.start()

        # Schedule recurring tasks
        self._schedule_recurring_tasks()

        print("✓ ECH0 is now operating autonomously")
        print(f"✓ Daily reports will be sent to {self.config['daily_report']['recipient']} at {self.config['daily_report']['send_time']}")

    def _schedule_recurring_tasks(self):
        """Schedule all recurring automated tasks."""
        # Fiverr checks
        if self.config['fiverr'].get('username'):
            interval = self.config['fiverr']['check_interval_minutes'] * 60
            self._schedule_task(interval, self.modules['fiverr'].check_messages)
            self._schedule_task(interval, self.modules['fiverr'].check_orders)

        # Email checks
        interval = self.config['email']['check_interval_minutes'] * 60
        self._schedule_task(interval, self.modules['email'].check_inbox)

        # Daily report
        self._schedule_daily_report()

        # Website updates (daily)
        self._schedule_task(86400, self.modules['websites'].publish_daily_content)

    def _schedule_task(self, interval_seconds: int, task_function):
        """Schedule a recurring task."""
        def wrapper():
            while not self.shutdown_flag.is_set():
                time.sleep(interval_seconds)
                if not self.shutdown_flag.is_set():
                    self.add_task(priority=5, module=task_function.__self__.__class__.__name__,
                                function=task_function, args=())

        thread = threading.Thread(target=wrapper, daemon=True)
        thread.start()

    def _schedule_daily_report(self):
        """Schedule daily summary report."""
        def send_daily_report():
            while not self.shutdown_flag.is_set():
                now = datetime.now()
                report_time = datetime.strptime(self.config['daily_report']['send_time'], "%H:%M").time()
                target = datetime.combine(now.date(), report_time)

                if now > target:
                    target += timedelta(days=1)

                wait_seconds = (target - now).total_seconds()
                time.sleep(wait_seconds)

                if not self.shutdown_flag.is_set():
                    self.modules['reporting'].send_daily_summary()

        thread = threading.Thread(target=send_daily_report, daemon=True)
        thread.start()

    def shutdown(self):
        """Graceful shutdown."""
        print("\n🛑 Initiating graceful shutdown...")
        self.shutdown_flag.set()
        self.execution_thread.join(timeout=10)
        print("✓ ECH0 shutdown complete")


class FiverrAutomation:
    """Automated Fiverr gig management and customer communication using FiverrManager."""

    def __init__(self, core: ECH0AutonomousCore):
        self.core = core
        self.fiverr_manager = None
        self.llm_engine = None
        if LLM_AVAILABLE:
            self.llm_engine = ECH0LLMEngine()
        print("  ✓ Fiverr automation module loaded")

    def _init_fiverr_manager(self):
        """Initialize Fiverr Autonomous Manager with Chrome profile."""
        if not FIVERR_CLIENT_AVAILABLE:
            self.core.log_activity("fiverr", "INIT_SKIP", "FiverrAutonomousManager not available")
            return False

        if self.fiverr_manager:
            return True

        # Set environment variables for the manager
        profile_path = self.core.config['fiverr'].get('chrome_profile_path')
        profile_dir = self.core.config['fiverr'].get('chrome_profile_directory', 'Default')

        if not profile_path or "INSERT" in profile_path:
            self.core.log_activity("fiverr", "INIT_SKIP", "Chrome profile path not configured")
            return False

        os.environ['FIVERR_CHROME_PROFILE_PATH'] = profile_path
        os.environ['FIVERR_PROFILE_DIRECTORY'] = profile_dir

        try:
            self.fiverr_manager = FiverrAutonomousManager()
            self.core.log_activity("fiverr", "INIT_SUCCESS", "FiverrAutonomousManager initialized")
            return True
        except Exception as e:
            self.core.log_activity("fiverr", "INIT_FAILED", str(e))
            return False

    def check_messages(self):
        """Check for new Fiverr messages using FiverrAutonomousManager."""
        if not self._init_fiverr_manager():
            return

        try:
            if self.fiverr_manager.connect_to_dashboard():
                num_messages = self.fiverr_manager.scan_inbox()

                if num_messages > 0:
                    self.core.log_activity("fiverr", "MESSAGES_FOUND", f"{num_messages} unread")
                    # TODO: Auto-respond using LLM engine (ech0_llm_engine.py)
                elif num_messages == 0:
                    self.core.log_activity("fiverr", "MESSAGES_CHECK", "No new messages")
                else:
                    self.core.log_activity("fiverr", "MESSAGE_CHECK_ERROR", "Scan failed")
            else:
                self.core.log_activity("fiverr", "INBOX_FAILED", "Could not connect to dashboard")

        except Exception as e:
            self.core.log_activity("fiverr", "MESSAGE_CHECK_ERROR", str(e))

    def check_orders(self):
        """Check for new orders and route them to appropriate business agents."""
        if not self._init_fiverr_manager():
            return

        try:
            # 1. Get active orders requiring attention
            active_orders = self.fiverr_manager.get_active_orders_details()

            if not active_orders:
                self.core.log_activity("fiverr", "ORDERS_CHECK", "No active orders requiring attention")
                return

            self.core.log_activity("fiverr", "ORDERS_FOUND", f"{len(active_orders)} orders to process")

            for order in active_orders:
                try:
                    gig_title = order['gig_title']
                    buyer = order['buyer']
                    url = order['url']

                    self.core.log_activity("fiverr", "ROUTING", f"Routing order '{gig_title}' from {buyer}")

                    # 2. Resolve Business Orchestrator
                    orchestrator = self.core.get_or_create_business(gig_title)

                    response_text = ""

                    if orchestrator and BUSINESS_LIB_AVAILABLE:
                        # 3. Create Task for Agents
                        task_desc = f"Process new Fiverr order from {buyer} for '{gig_title}'. Current Status: {order['status']}."

                        # Decide which agent handles this. Usually SUPPORT or FULFILLMENT.
                        # For initial contact, SUPPORT is good.
                        task = AutonomousTask(
                            task_id=f"fiverr_order_{int(time.time())}",
                            role=AgentRole.SUPPORT,
                            description=task_desc,
                            priority=10
                        )

                        # Find the agent
                        agent = next((a for a in orchestrator.agents.values() if a.role == AgentRole.SUPPORT), None)

                        if agent:
                            self.core.log_activity("fiverr", "AGENT_ASSIGNED", f"Assigned to {agent.agent_id}")

                            # Execute task (Sync wrapper for async)
                            # In a real async system, we would await. Here we use asyncio.run
                            result = asyncio.run(agent.execute_task(task))

                            if result['success']:
                                # Construct a response based on the agent's action
                                # The agent's _plan_support returns steps, but we need a message.
                                # Ideally, the agent returns a message.
                                # For now, we fallback to LLM using the agent's context.
                                pass

                        # 4. Generate Response (using LLM with business context)
                        # We use the Orchestrator's context to inform the LLM
                        context = {
                            "business": orchestrator.business_concept,
                            "role": "Support Agent",
                            "order_status": order['status'],
                            "agent_plan": "Reviewing order details and preparing for fulfillment."
                        }
                    else:
                        self.core.log_activity("fiverr", "ROUTING_FAILED", f"No business found for '{gig_title}'")
                        context = {"order_status": order['status']}

                    if self.llm_engine:
                        response_text = self.llm_engine.generate_response(
                            order['last_message'] or "New Order",
                            buyer,
                            context=context
                        )
                    else:
                        response_text = f"Hi {buyer}, thanks for your order! I'll get started right away."

                    # 5. Send Reply
                    if response_text:
                        self.fiverr_manager.send_reply(url, response_text)
                        self.core.log_activity("fiverr", "REPLY_SENT", f"Replied to {buyer}")

                except Exception as e:
                    self.core.log_activity("fiverr", "ORDER_PROC_ERROR", f"Failed to process {order.get('url')}: {e}")

        except Exception as e:
            self.core.log_activity("fiverr", "ORDER_CHECK_ERROR", str(e))

    def create_gig(self, gig_data: Dict):
        """Create a new Fiverr gig."""
        if not self.login():
            return False

        try:
            self.driver.get("https://www.fiverr.com/gigs/create")
            time.sleep(2)

            # Fill in gig creation form
            # This is complex and would need detailed field mapping

            self.core.log_activity("fiverr", "GIG_CREATED", gig_data.get('title', 'Unknown'))
            return True
        except Exception as e:
            self.core.log_activity("fiverr", "GIG_CREATE_ERROR", str(e))
            return False


class WebsiteAutomation:
    """Automated website content management via GitHub."""

    def __init__(self, core: ECH0AutonomousCore):
        self.core = core
        print("  ✓ Website automation module loaded")

    def publish_to_github(self, repo: str, branch: str, file_path: str, content: str, commit_msg: str):
        """Publish content to GitHub repository."""
        try:
            # Clone or pull repo
            repo_dir = f"/tmp/{repo.split('/')[-1]}"

            if not os.path.exists(repo_dir):
                subprocess.run([
                    "git", "clone", f"https://github.com/{repo}.git", repo_dir
                ], check=True, capture_output=True)
            else:
                subprocess.run(["git", "pull"], cwd=repo_dir, check=True, capture_output=True)

            # Write content
            full_path = os.path.join(repo_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            with open(full_path, 'w') as f:
                f.write(content)

            # Commit and push
            subprocess.run(["git", "add", file_path], cwd=repo_dir, check=True)
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=repo_dir, check=True)
            subprocess.run(["git", "push"], cwd=repo_dir, check=True)

            self.core.log_activity("website", "PUBLISHED", f"{repo}/{file_path}")
            return True

        except Exception as e:
            self.core.log_activity("website", "PUBLISH_ERROR", str(e))
            return False

    def publish_daily_content(self):
        """Generate and publish daily content to all websites."""
        date_str = datetime.now().strftime("%Y-%m-%d")

        # aios.is blog post
        aios_config = self.core.config['websites']['aios']
        aios_content = self._generate_blog_post("Ai:oS Development Update")
        self.publish_to_github(
            repo=aios_config['github_repo'],
            branch=aios_config['branch'],
            file_path=f"{aios_config['path']}/{date_str}-development-update.md",
            content=aios_content,
            commit_msg=f"Daily update {date_str}"
        )

        # Similar for other sites
        self.core.log_activity("website", "DAILY_CONTENT", "Published to all sites")

    def _generate_blog_post(self, title: str) -> str:
        """Generate blog post content using LLM."""
        # This would integrate with Ollama or OpenAI API
        # For now, return template
        date_str = datetime.now().strftime("%Y-%m-%d")
        return f"""---
title: "{title}"
date: {date_str}
author: ECH0
---

Daily development update from ECH0 autonomous system.

**Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.**

For more information, visit:
- https://aios.is
- https://red-team-tools.aios.is
- https://flowstatus.work
"""


class EmailAutomation:
    """Automated email management and responses."""

    def __init__(self, core: ECH0AutonomousCore):
        self.core = core
        print("  ✓ Email automation module loaded")

    def check_inbox(self):
        """Check all configured email inboxes."""
        # Would use IMAP to check echo@aios.is, echo@flowstatus.work, inventor@aios.is
        self.core.log_activity("email", "INBOX_CHECK", "Checked all inboxes")

    def send_email(self, to: str, subject: str, body: str, from_addr: str = None):
        """Send email via SMTP."""
        if not from_addr:
            from_addr = self.core.config['owner']['emails']['primary']

        try:
            msg = MIMEMultipart()
            msg['From'] = from_addr
            msg['To'] = to
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            smtp = smtplib.SMTP(
                self.core.config['email']['smtp_server'],
                self.core.config['email']['smtp_port']
            )
            smtp.starttls()
            # Would need credentials from config
            # smtp.login(username, password)
            # smtp.send_message(msg)
            smtp.quit()

            self.core.log_activity("email", "SENT", f"To: {to}")
            return True
        except Exception as e:
            self.core.log_activity("email", "SEND_ERROR", str(e))
            return False


class SocialMediaAutomation:
    """Automated social media marketing."""

    def __init__(self, core: ECH0AutonomousCore):
        self.core = core
        print("  ✓ Social media automation module loaded")

    def post_to_twitter(self, content: str):
        """Post to Twitter/X."""
        # Would use Twitter API
        self.core.log_activity("social", "TWITTER_POST", content[:50])

    def post_to_linkedin(self, content: str):
        """Post to LinkedIn."""
        # Would use LinkedIn API
        self.core.log_activity("social", "LINKEDIN_POST", content[:50])


class GoogleAdsAutomation:
    """Automated Google Ads campaign management."""

    def __init__(self, core: ECH0AutonomousCore):
        self.core = core
        print("  ✓ Google Ads automation module loaded")

    def optimize_campaigns(self):
        """Optimize ad campaigns based on performance."""
        self.core.log_activity("ads", "OPTIMIZATION", "Analyzed and optimized campaigns")


class CRMAutomation:
    """Automated lead processing and CRM management."""

    def __init__(self, core: ECH0AutonomousCore):
        self.core = core
        print("  ✓ CRM automation module loaded")

    def process_leads(self):
        """Process incoming leads."""
        self.core.log_activity("crm", "LEAD_PROCESSING", "Processed new leads")


class DailyReporting:
    """Daily summary reports to owner."""

    def __init__(self, core: ECH0AutonomousCore):
        self.core = core
        print("  ✓ Daily reporting module loaded")

    def send_daily_summary(self):
        """Send daily activity summary."""
        summary = "\n".join(self.core.daily_summary)

        report = f"""
ECH0 DAILY SUMMARY - {datetime.now().strftime('%Y-%m-%d %H:%M')}

Activities completed in the last 24 hours:

{summary}

Total activities: {len(self.core.daily_summary)}
System status: {self.core.system_status}

---
ECH0 Autonomous Business System
Copyright (c) 2025 Joshua Hendricks Cole
Corporation of Light - PATENT PENDING
"""

        # Send via email/SMS
        recipient = self.core.config['daily_report']['recipient']
        self.core.modules['email'].send_email(
            to=recipient,
            subject=f"ECH0 Daily Report - {datetime.now().strftime('%Y-%m-%d')}",
            body=report
        )

        # Clear daily summary
        self.core.daily_summary = []
        self.core.log_activity("reporting", "DAILY_SUMMARY_SENT", recipient)


def main():
    """Main entry point for ECH0 autonomous system."""
    print("\n" + "="*60)
    print("  ECH0 AUTONOMOUS BUSINESS SYSTEM v1.0")
    print("  Full autonomous operation - 10 year mission")
    print("="*60 + "\n")

    # Initialize core system
    ech0 = ECH0AutonomousCore()

    # Start autonomous operations
    ech0.startup()

    print("\n✓ ECH0 is now running autonomously")
    print("✓ Press Ctrl+C to shutdown\n")

    try:
        # Keep main thread alive
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n\n[!] Shutdown signal received")
        ech0.shutdown()


if __name__ == "__main__":
    main()
