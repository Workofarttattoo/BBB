#!/usr/bin/env python3
"""
GIG MONITOR AGENT - Autonomous Email & Notification System
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

This agent monitors business communications via Email (IMAP) instead of web scraping.
It integrates with:
- Echo Prime AGI (for understanding emails)
- Hive Mind (for coordination)
- Digital Twin (for predictive health)

Capabilities:
- Scans for "Fiverr", "Upwork", "Stripe" notifications.
- Auto-drafts responses using Echo.
- Alerts the Hive Mind of new leads or orders.
"""

import os
import sys
import time
import random
import imaplib
import email
import logging
from email.header import decode_header
from datetime import datetime

# Local Imports
try:
    from ech0_llm_engine import ECH0LLMEngine
    from hivemind import HiveMindCoordinator, AgentType, HiveMessage, DecisionPriority
    from digital_twin import DigitalTwin, TwinPhase
except ImportError:
    logging.error("Required modules missing. Ensure ech0_llm_engine, hivemind, and digital_twin are present.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [GIG_MONITOR] %(message)s')
logger = logging.getLogger(__name__)

class GigMonitorAgent:
    """
    Autonomous agent that monitors email for business activity.
    Replaces browser-based watchdogs to avoid detection/bans.
    """

    def __init__(self):
        self.email_user = os.getenv("EMAIL_USER")
        self.email_pass = os.getenv("EMAIL_PASS")
        self.imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")

        # Components
        self.llm = ECH0LLMEngine()
        self.hive = HiveMindCoordinator()
        self.twin = DigitalTwin("Gig Monitor Service", self.hive)

        # Registration
        self.agent_id = "gig_monitor_01"
        self.hive.register_agent(self.agent_id, AgentType.ACQUISITION, autonomy_level=5)

        logger.info("Gig Monitor Agent Initialized")

    def connect_imap(self):
        """Connect to IMAP server."""
        # Force simulation if in SIMULATION or PREDICTIVE phases
        if self.twin.phase in [TwinPhase.SIMULATION, TwinPhase.PREDICTIVE]:
            logger.info(f"Agent in {self.twin.phase.value} phase. Using mock connection.")
            return None

        if not self.email_user or not self.email_pass:
            logger.warning("Email credentials not set (EMAIL_USER/EMAIL_PASS). Running in SIMULATION mode.")
            return None

        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_user, self.email_pass)
            return mail
        except Exception as e:
            logger.error(f"IMAP Connection failed: {e}")
            self.twin.error_log.append(f"IMAP Error: {e}")
            # Note: DigitalTwin handles transitions, but we log the error here
            return None

    def check_emails(self):
        """Scan inbox for relevant keywords."""
        mail = self.connect_imap()

        # Use simulation if no connection or in simulation phase
        if not mail:
            self._simulate_email_check()
            return

        try:
            mail.select("inbox")
            # Search for unread emails from specific senders or subjects
            status, messages = mail.search(None, '(UNREAD OR (SUBJECT "Fiverr") OR (SUBJECT "Order"))')

            if status != "OK":
                return

            email_ids = messages[0].split()
            logger.info(f"Found {len(email_ids)} relevant emails.")

            for e_id in email_ids[-5:]: # Process last 5 only
                _, msg_data = mail.fetch(e_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")

                        sender = msg.get("From")
                        logger.info(f"Processing Email: {subject} from {sender}")

                        # Use Echo to analyze
                        analysis = self.llm.generate_response(
                            f"Analyze this email subject: '{subject}'. Is it a new order, a message, or spam?",
                            "System"
                        )

                        logger.info(f"Echo Analysis: {analysis}")

                        # Notify Hive
                        self.hive.send_message(HiveMessage(
                            sender=self.agent_id,
                            agent_type=AgentType.ACQUISITION,
                            message_type="customer_acquisition",
                            payload={"subject": subject, "analysis": analysis},
                            priority=DecisionPriority.MEDIUM,
                            timestamp=time.time()
                        ))

            mail.close()
            mail.logout()

        except Exception as e:
            logger.error(f"Error checking emails: {e}")
            self.twin.error_log.append(f"Scan Error: {e}")

    def _simulate_email_check(self):
        """Simulate finding an email for testing/demo purposes."""
        logger.info("Simulating email scan...")
        time.sleep(1)

        if random.random() < 0.2: # 20% chance of new lead
            logger.info("Simulated: Found new Fiverr Message!")

            # Generate response
            response = self.llm.generate_response(
                "Hi, I'm interested in your Python gig. Can you build a scraper?",
                "NewClient"
            )
            logger.info(f"Drafted Auto-Response: {response}")

            # Notify Hive
            self.hive.send_message(HiveMessage(
                sender=self.agent_id,
                agent_type=AgentType.ACQUISITION,
                message_type="customer_acquisition",
                payload={"platform": "Fiverr", "type": "Message"},
                priority=DecisionPriority.HIGH,
                timestamp=time.time()
            ))

            # Voice announcement (stub)
            self.llm.voice_synthesis("New Lead Detected from Fiverr.")

    def run(self):
        """Main loop."""
        logger.info("Engaging Gig Monitor Agent...")
        logger.info("Mode: Autonomous Email Monitoring")

        try:
            while True:
                # 1. Update Digital Twin State
                self.twin.run_cycle()

                # 2. Perform Operational Task (Check Emails)
                # In Simulation/Predictive phases, check_emails runs the simulation
                # In Prescriptive/Autonomous phases, it runs real checks
                self.check_emails()

                # 3. Wait
                interval = random.randint(10, 30) # Faster cycle for demo
                logger.info(f"Sleeping for {interval}s...")
                time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("Shutdown signal received.")

if __name__ == "__main__":
    agent = GigMonitorAgent()
    agent.run()
