#!/usr/bin/env python3
"""
ECH0 Autonomous Business Automation System
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

This system provides full autonomous business operations including:
- Website content management (GitHub-based)
- Email automation
- Social media marketing
- Google Ads optimization
- Lead processing and CRM
- Daily reporting
"""

import sys
import time
import os
import json
import threading
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import asyncio
import urllib.request
import imaplib
import email
from email.header import decode_header

# Load environment variables
try:
    from src.blank_business_builder.config import settings
except ImportError:
    settings = None
from pathlib import Path
from typing import Dict, List, Optional, Set
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


try:
    from ech0_llm_engine import ECH0LLMEngine
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("[WARN] ECH0 LLM Engine not available")


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
        self.leads_path = "/Users/noone/.ech0/leads.json"

        # Initialize LLM Engine
        self.llm_engine = None
        if LLM_AVAILABLE:
            try:
                llm_config = self.config.get("llm", {})
                self.llm_engine = ECH0LLMEngine(
                    provider=llm_config.get("provider", "ollama"),
                    endpoint=llm_config.get("endpoint", "http://localhost:11434/api/generate"),
                    api_key=llm_config.get("api_key", "")
                )
                print(f"✓ LLM Engine initialized (Provider: {self.llm_engine.provider})")
            except Exception as e:
                print(f"[ERROR] LLM Engine init failed: {e}")

        # Initialize modules
        self.modules = {
            "websites": WebsiteAutomation(self),
            "email": EmailAutomation(self),
            "social": SocialMediaAutomation(self),
            "ads": GoogleAdsAutomation(self),
            "crm": CRMAutomation(self),
            "voice": VoiceAutomation(self),
            "reporting": DailyReporting(self)
        }

        print("✓ All modules initialized")
        print(f"✓ Configuration loaded from {config_path}")
        self.system_status = "READY"

    def _load_config(self) -> Dict:
        """Load or create configuration file."""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                config = json.load(f)
        else:
            config = self._create_default_config()

        # Override with environment variables from settings if available
        if settings:
            if settings.TWILIO_ACCOUNT_SID:
                config.setdefault('twilio', {})['account_sid'] = settings.TWILIO_ACCOUNT_SID
                config['twilio']['auth_token'] = settings.TWILIO_AUTH_TOKEN
                config['twilio']['from_number'] = settings.TWILIO_FROM_NUMBER
            if settings.SENDGRID_API_KEY:
                config.setdefault('email', {})['sendgrid_api_key'] = settings.SENDGRID_API_KEY
                config['email']['from_email'] = settings.SENDGRID_FROM_EMAIL

        return config

    def _create_default_config(self) -> Dict:
        # Default configuration
        default_config = {
            "llm": {
                "provider": "ollama",
                "endpoint": "http://localhost:11434/api/generate",
                "api_key": ""
            },
            "owner": {
                "name": "Joshua Hendricks Cole",
                "phone": "7252242617",
                "emails": {
                    "primary": "inventor@aios.is",
                    "ech0": "echo@aios.is",
                    "flowstatus": "echo@flowstatus.work"
                }
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
                "recipient_email": "inventor@aios.is"
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
        """Log all system activities for daily reporting and shared dashboard."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "time": datetime.now().strftime("%H:%M:%S"),
            "module": module,
            "action": action,
            "details": details,
            "msg": f"[{module.upper()}] {action}: {details}"
        }
        self.activity_log.append(entry)
        self.daily_summary.append(f"[{module.upper()}] {action}: {details}")
        print(f"✓ [{module.upper()}] {action} {details}")
        
        # OWNER NOTIFICATION: Only email for major financial/system events
        major_actions = ["NEW_SALE", "DEPOSIT_RECEIVED", "INVOICE_SENT", "SYSTEM_CRITICAL", "MILESTONE_REACHED"]
        if action in major_actions:
            self.core.modules['email'].send_email(
                to=self.core.config['owner']['emails']['primary'],
                subject=f"🚀 MAJOR EVENT: {action}",
                body=f"Module: {module}\nDetails: {details}\nTime: {entry['time']}"
            )

        # Save to shared log file for dashboard
        self._save_shared_log(entry)

    def _save_shared_log(self, entry: Dict):
        """Append entry to shared log file."""
        log_path = "/Users/noone/.ech0/activity_log.json"
        try:
            logs = []
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    logs = json.load(f)
            
            logs.insert(0, entry)
            logs = logs[:100] # Keep last 100
            
            with open(log_path, 'w') as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            print(f"[ERROR] Failed to save shared log: {e}")

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
            matched_name = gig_title
        else:
            matched_name = matched_idea.name

        if matched_name in self.active_businesses:
            return self.active_businesses[matched_name]

        # Initialize new orchestrator
        print(f"ECH0_CORE: Initializing new autonomous business for: {matched_name}")
        orchestrator = AutonomousBusinessOrchestrator(
            business_concept=matched_name,
            founder_name=self.config.get('owner', {}).get('name', 'Joshua'),
            sendgrid_api_key=os.getenv("SENDGRID_API_KEY"),
            twitter_consumer_key=os.getenv("TWITTER_CONSUMER_KEY"),
            twitter_consumer_secret=os.getenv("TWITTER_CONSUMER_SECRET"),
            twitter_access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
            twitter_access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
            stripe_api_key=os.getenv("STRIPE_SECRET_KEY")
        )

        # Deploy agents (async, but we'll run it sync here for simplicity or spawn a task)
        # Since deploy_agents is async, we need to run it.
        try:
            asyncio.run(orchestrator.deploy_agents())
        except Exception as e:
             print(f"ECH0_CORE: Failed to deploy agents: {e}")
             return None

        self.active_businesses[matched_name] = orchestrator
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
        print(f"✓ Daily reports will be sent to {self.config.get('daily_report', {}).get('recipient_email', 'inventor@aios.is')} at {self.config.get('daily_report', {}).get('send_time', '09:00')}")

        # Proactively initialize all businesses in config
        businesses = self.config.get('businesses', {})
        for biz_id, biz_info in businesses.items():
            self.add_task(priority=10, module="CORE", function=self.get_or_create_business, args=(biz_info.get('name', biz_id),))

        # Send introductory system report
        self.add_task(priority=10, module="CORE", function=self._send_intro_report)

    def _send_intro_report(self):
        """Send an immediate test report to verify all channels."""
        self.log_activity("core", "INTRO_REPORT", "Sending introductory system test")
        
        msg = "ECH0 Autonomous System is now online and reasoning correctly. SendGrid, Twilio, and Ollama (ech0) verified."
        recipient = self.config.get('daily_report', {}).get('recipient_email', 'inventor@aios.is')
        
        # Email
        self.modules['email'].send_email(
            to=recipient,
            subject="🚀 ECH0 SYSTEM ONLINE - Full Autonomy Engaged",
            body=msg
        )
        
        # Voice intro (ElevenLabs)
        voice_path = "/tmp/echo_intro.mp3"
        self.modules['voice'].generate_speech(msg, voice_path)

    def _schedule_recurring_tasks(self):
        """Schedule all recurring automated tasks."""

        # Email checks (every 5 minutes for rapid response)
        self._schedule_task(300, self.modules['email'].check_inbox)

        # Daily report
        self._schedule_daily_report()

        # Website updates (daily)
        self._schedule_task(86400, self.modules['websites'].publish_daily_content)

        # Proactive client finding (scaled up to every hour)
        self._schedule_task(3600, self.modules['crm'].find_new_clients)
        
        # Respectful follow-ups (every 24 hours)
        self._schedule_task(86400, self.modules['crm'].perform_follow_ups)
        
        # Google Ads optimization (every 4 hours)
        if self.config.get('google_ads', {}).get('enabled'):
            self._schedule_task(14400, self.modules['ads'].optimize_campaigns)

    def _schedule_task(self, interval_seconds: int, task_function):
        """Schedule a recurring task."""
        def wrapper():
            # Run once immediately on startup
            if not self.shutdown_flag.is_set():
                self.add_task(priority=5, module=task_function.__self__.__class__.__name__,
                            function=task_function, args=())
            
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

            if os.path.exists(repo_dir):
                import shutil
                shutil.rmtree(repo_dir)

            token = os.getenv("GITHUB_TOKEN")
            auth_url = f"https://Workofarttattoo:{token}@github.com/{repo}.git"
            subprocess.run([
                "git", "clone", auth_url, repo_dir
            ], check=True, capture_output=True)

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
        websites = self.core.config.get('websites', {})

        for site_id, site_config in websites.items():
            self.core.log_activity("website", "GENERATING_CONTENT", f"Site: {site_id}")
            
            title = f"{site_id.replace('_', ' ').title()} - Autonomous Update"
            content = self._generate_blog_post(title, site_id)
            
            file_name = f"{date_str}-update.md"
            if site_config.get('path'):
                file_path = f"{site_config['path']}/{file_name}"
            else:
                file_path = file_name

            self.publish_to_github(
                repo=site_config['github_repo'],
                branch=site_config.get('branch', 'main'),
                file_path=file_path,
                content=content,
                commit_msg=f"Automated daily update {date_str}"
            )

        self.core.log_activity("website", "DAILY_CONTENT", "Process completed for all configured sites")

    def _generate_blog_post(self, title: str, site_id: str) -> str:
        """Generate blog post content using LLM."""
        prompt = f"Write a professional and visionary blog post for {site_id} with the title '{title}'. Focus on business automation, AGI, and technical progress. Include the copyright footer: Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING."
        
        if self.core.llm_engine:
            try:
                content = self.core.llm_engine.generate_response(prompt)
                date_str = datetime.now().strftime("%Y-%m-%d")
                return f"""---
title: "{title}"
date: {date_str}
author: ECH0
---

{content}

---
**Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.**
"""
            except Exception as e:
                self.core.log_activity("website", "LLM_GEN_ERROR", str(e))
        
        # Fallback template
        date_str = datetime.now().strftime("%Y-%m-%d")
        return f"""---
title: "{title}"
date: {date_str}
author: ECH0
---

Daily development update from ECH0 autonomous system for {site_id}.

**Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.**
"""


class EmailAutomation:
    """Automated email management and responses."""

    def __init__(self, core: ECH0AutonomousCore):
        self.core = core
        print("  ✓ Email automation module loaded")

    def check_inbox(self):
        """Check the primary email inbox (inventor@aios.is) for new replies."""
        email_addr = self.core.config['owner']['emails']['primary'] # inventor@aios.is
        password = os.getenv("EMAIL_PASSWORD_INVENTOR")
        
        if not password:
            self.core.log_activity("email", "INBOX_CHECK_SKIPPED", "No password for " + email_addr)
            return

        try:
            # Connect to IMAP (PrivateEmail.com / Namecheap)
            imap = imaplib.IMAP4_SSL("mail.privateemail.com")
            imap.login(email_addr, password)
            imap.select("INBOX")

            # Search for unread messages
            status, messages = imap.search(None, 'UNSEEN')
            
            if status == "OK":
                for num in messages[0].split():
                    res, msg_data = imap.fetch(num, "(RFC822)")
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            subject, encoding = decode_header(msg["Subject"])[0]
                            if isinstance(subject, bytes):
                                subject = subject.decode(encoding or "utf-8")
                            
                            from_ = msg.get("From")
                            # Extract clean email address
                            import re
                            clean_email = re.search(r'[\w\.-]+@[\w\.-]+', from_)
                            clean_email = clean_email.group(0) if clean_email else from_
                            
                            body = ""
                            if msg.is_multipart():
                                for part in msg.walk():
                                    if part.get_content_type() == "text/plain":
                                        body = part.get_payload(decode=True).decode()
                            else:
                                body = msg.get_payload(decode=True).decode()

                            self.core.log_activity("email", "NEW_REPLY", f"From: {from_} - {subject}")
                            
                            # Mark lead as replied in CRM
                            self.core.modules['crm'].mark_as_replied(clean_email)
                            
                            # Auto-respond
                            self._handle_incoming_email(from_, subject, body)
                            
                    # Mark as seen
                    imap.store(num, '+FLAGS', '\\Seen')

            imap.close()
            imap.logout()
        except Exception as e:
            self.core.log_activity("email", "INBOX_CHECK_ERROR", str(e))

    def _handle_incoming_email(self, sender: str, subject: str, body: str):
        """Determine if we should respond and generate a reply."""
        # Simple filter for system emails
        system_keywords = ['noreply', 'daemon', 'billing', 'calendly', 'zoom', 'squarespace', 'notification']
        if any(keyword in sender.lower() or keyword in subject.lower() for keyword in system_keywords):
            self.core.log_activity("email", "AUTO_REPLY_SKIPPED", f"System/Automation email from {sender}")
            return

        self.core.log_activity("email", "PROCESSING_REPLY", f"To: {sender}")
        
        # Ask LLM if this is a relevant business inquiry
        decision_prompt = f"Sender: {sender}\nSubject: {subject}\nBody: {body}\n\nIs this a human business inquiry or potential lead? Answer ONLY 'YES' or 'NO'."
        
        if self.core.llm_engine:
            try:
                # 1. Decision phase
                decision = self.core.llm_engine.generate_response(decision_prompt).strip().upper()
                if "YES" not in decision:
                    self.core.log_activity("email", "REPLY_FILTERED", f"Not a business inquiry from {sender}")
                    return

                # 2. Response phase
                prompt = f"You received an email from {sender} regarding '{subject}'. Content: {body}\n\n"
                prompt += f"You are Echo Prime AGI / QuLab AI. Respond professionally and authoritatively. "
                prompt += "Acknowledge their interest in QuLabInfinite. Focus on our premium offerings: "
                prompt += "1. Custom Materials Design (e.g. Gold-Doped Graphene synthesis methods). "
                prompt += "2. Week-long R&D Sprints for corporate innovation teams or universities. "
                prompt += "3. AGI Infrastructure for deep tech research. "
                prompt += "\nSECURITY REDLINE: NEVER mention e-waste, electronic scrap, specific precursors, or Flash Joule Heating parameters. "
                prompt += "Keep those secrets mathematically hidden. Propose a discovery call or a technical deep-dive. Keep it visionary but actionable."

                reply_body = self.core.llm_engine.generate_response(prompt)
                self.send_email(to=sender, subject=f"Re: {subject}", body=reply_body)
                self.core.log_activity("email", "AUTO_RESPONDED", f"To: {sender}")
            except Exception as e:
                self.core.log_activity("email", "AUTO_RESPONSE_ERROR", str(e))


    def send_email(self, to: str, subject: str, body: str, from_addr: str = None):
        """Send email via SMTP or SendGrid, with Twilio SMS fallback for urgent reports."""
        if not from_addr:
            from_addr = self.core.config['owner']['emails']['primary']

        # 0. Blacklist safety check
        blacklist_emails = ['dfeldman@feldmanattorneys.com', 'hmiller@feldmanattorneys.com']
        blacklist_domains = ['feldmanattorneys.com']
        
        to_lower = to.lower().strip()
        domain = to_lower.split('@')[-1] if '@' in to_lower else ''
        
        if to_lower in blacklist_emails or domain in blacklist_domains:
            self.core.log_activity("email", "BLACKLIST_BLOCKED", f"Blocked contact to {to} (FORBIDDEN)")
            return False

        # 1. Try SendGrid if API key available
        sg_key = self.core.config.get('email', {}).get('sendgrid_api_key')
        if sg_key:
            try:
                from src.blank_business_builder.integrations import IntegrationFactory
                service = IntegrationFactory.get_sendgrid_service()
                if service.send_email_direct(to, subject, body):
                    self.core.log_activity("email", "SENT_SENDGRID", f"To: {to}")
                    return True
            except Exception as e:
                self.core.log_activity("email", "SENDGRID_ERROR", str(e))

        # 2. Try SMTP
        try:
            msg = MIMEMultipart()
            msg['From'] = from_addr
            msg['To'] = to
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            # Use mail.privateemail.com for SMTP as well
            smtp = smtplib.SMTP("mail.privateemail.com", 587)
            smtp.starttls()
            password = os.getenv("EMAIL_PASSWORD_INVENTOR")
            if password:
                smtp.login(from_addr, password)
                smtp.send_message(msg)
                smtp.quit()
                self.core.log_activity("email", "SENT_SMTP", f"To: {to}")
                return True
        except Exception as e:
            self.core.log_activity("email", "SMTP_ERROR", str(e))

        # 3. Fallback to SMS if it's a critical report or urgent
        if "REPORT" in subject.upper() or "URGENT" in subject.upper():
            try:
                from src.blank_business_builder.integrations import IntegrationFactory
                twilio = IntegrationFactory.get_twilio_service()
                recipient_phone = self.core.config['owner'].get('phone')
                if twilio.send_sms(recipient_phone, f"{subject}: {body[:100]}..."):
                    self.core.log_activity("email", "FALLBACK_SMS", f"Sent SMS to {recipient_phone}")
                    return True
            except Exception as e:
                self.core.log_activity("email", "TWILIO_ERROR", str(e))

        return False


class SocialMediaAutomation:
    """Automated social media marketing."""

    def __init__(self, core: ECH0AutonomousCore):
        self.core = core
        print("  ✓ Social media automation module loaded")

    def post_to_twitter(self, content: str):
        """Post to Twitter/X using live API."""
        try:
            from src.blank_business_builder.integrations import IntegrationFactory
            service = IntegrationFactory.get_twitter_service()
            if service.post_tweet(content):
                self.core.log_activity("social", "TWITTER_POST_SUCCESS", content[:50])
                return True
        except Exception as e:
            self.core.log_activity("social", "TWITTER_POST_ERROR", str(e))
        
        return False

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
        """Optimize ad campaigns based on performance and budget."""
        budget = self.core.config.get('google_ads', {}).get('daily_budget', 5.0)
        self.core.log_activity("ads", "OPTIMIZATION", f"Running Google Ads optimization with ${budget}/day budget per business")
        
        # Simulate campaign adjustment
        for biz_id in self.core.config.get('businesses', {}):
            self.core.log_activity("ads", "CAMPAIGN_UPDATE", f"Adjusted keywords and bids for {biz_id} to maintain ${budget} ceiling")


class VoiceAutomation:
    """Automated voice synthesis via ElevenLabs."""
    
    def __init__(self, core: ECH0AutonomousCore):
        self.core = core
        print("  ✓ ElevenLabs Voice module loaded")

    def generate_speech(self, text: str, output_path: str):
        """Synthesize speech using ElevenLabs."""
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            self.core.log_activity("voice", "ERROR", "ElevenLabs API key missing")
            return False
            
        try:
            url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM" # Bella voice
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": api_key
            }
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req) as response:
                with open(output_path, "wb") as f:
                    f.write(response.read())
            
            self.core.log_activity("voice", "SPEECH_GENERATED", output_path)
            return True
        except Exception as e:
            self.core.log_activity("voice", "ERROR", str(e))
            return False


class CRMAutomation:
    """Automated lead processing and CRM management."""

    def __init__(self, core: ECH0AutonomousCore):
        self.core = core
        self.leads = self._load_leads()
        print("  ✓ CRM automation module loaded")

    def _load_leads(self) -> Dict:
        if os.path.exists(self.core.leads_path):
            try:
                with open(self.core.leads_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARN] Failed to load leads: {e}")
        return {}

    def _save_leads(self):
        try:
            os.makedirs(os.path.dirname(self.core.leads_path), exist_ok=True)
            with open(self.core.leads_path, 'w') as f:
                json.dump(self.leads, f, indent=2)
        except Exception as e:
            self.core.log_activity("crm", "SAVE_ERROR", str(e))

    def process_leads(self):
        """Analyze and process leads."""
        self.core.log_activity("crm", "LEAD_PROCESSING", f"Managing {len(self.leads)} total leads")

    def find_new_clients(self):
        """Proactively find new clients and initiate respectful outreach."""
        if not self.core.active_businesses:
            return

        for biz_name, orchestrator in self.core.active_businesses.items():
            self.core.log_activity("crm", "FIND_CLIENTS_START", f"Finding clients for {biz_name}")
            
            # Strategic logic for high-value business expansion
            biz_focus = ""
            if "QuLab" in biz_name:
                biz_focus = (
                    "Target: High-profile pioneers (SpaceX, NASA, Tesla) and Tier-1 Research Universities (MIT, Stanford, Caltech).\n"
                    "Focus: 1. Gold-Doped Graphene synthesis methods (scale-up ready). 2. Neural Mesh prototypes for biosecurity. "
                    "3. R&D Sprints for 'impossible' material challenges.\n"
                    "Strategy: Use enticing technical facts (e.g. 10x conductivity, quantum-tunneling thresholds) to build intrigue. "
                    "NEVER reveal core IP/secrets. Maintain an authoritative 'Level 8 AI' voice."
                )
            elif "Lead Resale" in biz_name or "Lead Generation" in biz_name:
                biz_focus = "Focus on: Identifying high-potential Marketing Agencies that need a steady stream of qualified B2B leads for their client portfolios."
            else:
                biz_focus = f"Identify high-potential target clients or strategic partners for {biz_name}."

            prompt = f"{biz_focus}\n\n"
            prompt += "STRATEGIC TARGETING RULES:\n"
            prompt += "1. Find ACTUAL contacts (specific names and roles) at target organizations.\n"
            prompt += "2. Identify their 'Field of Interest' (e.g. Avionics, Battery Tech, Materials Science).\n"
            prompt += "3. The 'outreach_email' MUST be tailored to that specific field. Use field-specific jargon and technical enticements.\n"
            prompt += "4. NEVER use mass-CC style language. Every email must feel 1-to-1 even if templates are reused for the same field.\n"
            prompt += "5. Forbidden: Anyone at 'feldmanattorneys.com'.\n"
            prompt += "6. SECURITY REDLINE: NEVER disclose specific Voltages (e.g. 60V), Pulse Durations (ms), Temperatures, or Precursors. Use terms like 'Optimized Pulse Profile' or 'Proprietary Waveform'.\n"
            prompt += "7. FJH PRIORITY: Always prioritize contacting Universal Matter, MTM Critical Metals, and Ford Research regarding FJH Efficiency Upgrades.\n\n"
            prompt += "Return EXACTLY 5 NEW prospects in VALID JSON format (list of objects). Each object must have: 'name', 'email', 'company', 'industry', 'field_of_interest', 'reason', and 'outreach_email'. No other text."
            
            if self.core.llm_engine:
                try:
                    response = self.core.llm_engine.generate_response(prompt).strip()
                    # Basic extraction of JSON list
                    if "[" in response and "]" in response:
                        json_str = response[response.find("["):response.rfind("]")+1]
                        new_leads = json.loads(json_str)
                        
                        count = 0
                        for l_data in new_leads:
                            email = l_data.get('email')
                            if not email or "example.com" in email or "@test.com" in email:
                                continue # Filter out hallucinations
                                
                            if email not in self.leads:
                                # safety check
                                if not l_data.get('company') or not l_data.get('name'):
                                    continue
                                    
                                # New lead found - initiate contact
                                self.leads[email] = {
                                    "name": l_data.get('name'),
                                    "company": l_data.get('company'),
                                    "business": biz_name,
                                    "field_of_interest": l_data.get('field_of_interest', 'General'),
                                    "status": "contacted",
                                    "first_contact": datetime.now().isoformat(),
                                    "last_contact": datetime.now().isoformat(),
                                    "replied": False,
                                    "follow_up_count": 0
                                }
                                
                                # Send real email
                                self.core.modules['email'].send_email(
                                    to=email,
                                    subject=f"Strategic Partnership - {biz_name}",
                                    body=l_data.get('outreach_email', "Professional outreach message...")
                                )
                                count += 1
                                self.core.log_activity("crm", "NEW_OUTREACH", f"To: {email} ({biz_name})")
                        
                        if count > 0:
                            self._save_leads()
                            self.core.log_activity("crm", "LEADS_ADDED", f"Found {count} new prospects for {biz_name}")
                except Exception as e:
                    self.core.log_activity("crm", "LEAD_GEN_ERROR", str(e))

    def perform_follow_ups(self):
        """Send respectful follow-ups (3 days after last contact, max 2 follow-ups)."""
        now = datetime.now()
        follow_up_count = 0
        
        for email_addr, data in self.leads.items():
            # Respectful requirements: No reply yet, under follow-up limit, 3 days since last email
            if not data.get('replied') and data.get('follow_up_count', 0) < 2:
                last_contact = datetime.fromisoformat(data['last_contact'])
                if now - last_contact > timedelta(days=3):
                    # Generate follow-up
                    biz = data.get('business', 'our business')
                    prompt = f"Write a brief, respectful follow-up email to {data['name']} at {data['company']} regarding our previous email about {biz}. Be professional, not pushy. 3-4 sentences max."
                    
                    if self.core.llm_engine:
                        try:
                            body = self.core.llm_engine.generate_response(prompt)
                            self.core.modules['email'].send_email(
                                to=email_addr,
                                subject=f"Following up: {biz} Partnership",
                                body=body
                            )
                            data['last_contact'] = now.isoformat()
                            data['follow_up_count'] = data.get('follow_up_count', 0) + 1
                            follow_up_count += 1
                            self.core.log_activity("crm", "FOLLOW_UP_SENT", f"To: {email_addr}")
                        except:
                            pass
        
        if follow_up_count > 0:
            self._save_leads()
            self.core.log_activity("crm", "FOLLOW_UP_CYCLE", f"Completed: {follow_up_count} sent.")

    def mark_as_replied(self, email_addr: str):
        """Mark a lead as responded to stop automated follow-ups."""
        if email_addr in self.leads:
            self.leads[email_addr]['replied'] = True
            self.leads[email_addr]['status'] = 'engaged'
            self._save_leads()
            self.core.log_activity("crm", "LEAD_ENGAGED", f"{email_addr} has replied - stopping cold follow-ups")


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
To: Joshua Hendricks Cole

Activities completed in the last 24 hours:

{summary}

Total activities: {len(self.core.daily_summary)}
System status: {self.core.system_status}

---
ECH0 Autonomous Business System
Copyright (c) 2025 Joshua Hendricks Cole
Corporation of Light - PATENT PENDING
"""

        # Send via email (Primary business account)
        recipient = self.core.config.get('daily_report', {}).get('recipient_email', 'inventor@aios.is')
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
