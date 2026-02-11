#!/usr/bin/env python3
"""
MODULE 3: FIVERR_AUTONOMOUS_MANAGER
PROTOCOL: ech0 / Hendricks-Cole-231
STATUS: OPERATIONAL / MANAGEMENT-ONLY
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

DEPENDENCIES:
pip install selenium webdriver-manager
"""

import os
import sys
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys  # Added for auto-response typing
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Import human behavior simulator
try:
    from human_behavior_simulator import HumanBehaviorSimulator
    HUMAN_BEHAVIOR_AVAILABLE = True
except ImportError:
    HUMAN_BEHAVIOR_AVAILABLE = False
    print("[WARN] Human behavior simulator not available - using basic automation")

# --- CONFIGURATION ---
# CRITICAL: Set this to your ACTUAL Chrome Profile path.
# Mac Example: "/Users/yourname/Library/Application Support/Google/Chrome"
# Windows Example: r"C:\Users\yourname\AppData\Local\Google\Chrome\User Data"
CHROME_PROFILE_PATH = os.getenv("FIVERR_CHROME_PROFILE_PATH", "INSERT_YOUR_PROFILE_PATH_HERE")
PROFILE_DIRECTORY = os.getenv("FIVERR_PROFILE_DIRECTORY", "Default")  # Usually 'Default' or 'Profile 1'

class FiverrAutonomousManager:
    """
    Autonomous Agent for managing an existing, logged-in Fiverr session.
    Does NOT create gigs. DOES handle messages and orders.
    """
    def __init__(self):
        print("ECH0_FIVERR: Initializing Management Agent...")

        if "INSERT" in CHROME_PROFILE_PATH:
            print("ECH0_FIVERR: [HALT] You must set the CHROME_PROFILE_PATH.")
            print("ECH0_FIVERR: Set environment variable: FIVERR_CHROME_PROFILE_PATH")
            sys.exit(1)

        self.options = Options()
        # This attaches the agent to your REAL browser profile
        self.options.add_argument(f"user-data-dir={CHROME_PROFILE_PATH}")
        self.options.add_argument(f"profile-directory={PROFILE_DIRECTORY}")

        # Stealth flags to reduce bot detection
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)

        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=self.options
            )
            self.wait = WebDriverWait(self.driver, 20)

            # Initialize human behavior simulator
            if HUMAN_BEHAVIOR_AVAILABLE:
                self.human = HumanBehaviorSimulator(self.driver)
                print("ECH0_FIVERR: Agent attached with HUMAN BEHAVIOR MODE enabled.")
            else:
                self.human = None
                print("ECH0_FIVERR: Agent attached (basic automation mode).")

        except Exception as e:
            print(f"ECH0_FIVERR: [CRITICAL] Browser attachment failed: {e}")
            print("Hint: Make sure all other Chrome windows are CLOSED.")
            sys.exit(1)

    def connect_to_dashboard(self):
        """Navigates to the dashboard and verifies the session is alive."""
        print("ECH0_FIVERR: Establishing connection to HQ...")
        try:
            self.driver.get("https://www.fiverr.com/users/dashboard")

            # Human-like page arrival behavior
            if self.human:
                self.human.natural_page_arrival_behavior()
            else:
                time.sleep(random.uniform(1, 3))

            # Look for a dashboard element to confirm login
            # (e.g., the 'Inbox' or 'Dashboard' text)
            if "login" in self.driver.current_url:
                print("ECH0_FIVERR: [ALERT] Session expired. Please log in manually, then restart agent.")
                return False

            print("ECH0_FIVERR: Connection confirmed. We are live.")
            return True
        except Exception as e:
            print(f"ECH0_FIVERR: [ERROR] Connection failed: {e}")
            return False

    def scan_inbox(self):
        """Checks for unread messages in the inbox."""
        print("ECH0_FIVERR: Scanning communications...")
        self.driver.get("https://www.fiverr.com/inbox")

        # Human-like page arrival
        if self.human:
            self.human.natural_page_arrival_behavior()
            # Random mouse movement (fidgeting)
            self.human.random_mouse_movement()
        else:
            time.sleep(random.uniform(3, 6))

        try:
            # This selector looks for the 'unread' dot/class in the message list
            # Note: Selectors change. Vision-based AI (Level 9) updates this dynamically.
            unread_msgs = self.driver.find_elements(By.CSS_SELECTOR, ".unread")

            # Simulate reading/scanning behavior
            if self.human and unread_msgs:
                # Look at the inbox inefficiently first
                all_messages = self.driver.find_elements(By.CSS_SELECTOR, "[class*='message'], [class*='conversation']")
                if len(all_messages) > 3:
                    # Don't immediately focus on unread - look at others first
                    distractions = random.sample(all_messages[:5], min(2, len(all_messages)))
                    for msg in distractions:
                        try:
                            self.human.human_move_to_element(msg)
                            time.sleep(random.uniform(0.5, 1.2))
                        except:
                            pass  # Element might not be interactable

            if unread_msgs:
                count = len(unread_msgs)
                print(f"ECH0_FIVERR: {count} unread message(s) detected.")
                return count
            else:
                print("ECH0_FIVERR: Inbox clear.")
                return 0
        except Exception as e:
            print(f"ECH0_FIVERR: Inbox scan clear (No indicators found): {e}")
            return 0

    def respond_to_unread_messages(self, llm_response_callback):
        """
        Iterates through unread messages and responds using the provided generator function.

        Args:
            llm_response_callback: function(message_text, context) -> response_text
        """
        print("ECH0_FIVERR: Checking for unread messages to respond...")

        try:
            self.driver.get("https://www.fiverr.com/inbox")
            time.sleep(random.uniform(3, 5))

            # Find unread indicators - based on existing codebase pattern
            unread_indicators = self.driver.find_elements(By.CSS_SELECTOR, ".unread")

            if not unread_indicators:
                print("ECH0_FIVERR: No unread messages found to respond to.")
                return

            print(f"ECH0_FIVERR: Found {len(unread_indicators)} unread threads. Processing...")

            # We process one by one, returning to inbox each time to refresh state
            # Limit to 5 per batch to avoid getting stuck
            max_process = 5
            processed_count = 0

            while processed_count < max_process:
                # Re-find unread items on each iteration as page changes
                unread_items = self.driver.find_elements(By.CSS_SELECTOR, ".unread")

                if not unread_items:
                    break

                # Click the first unread item
                try:
                    # Often the .unread is a dot inside the list item, we might need to click the parent
                    # For safety, we click the element itself or its parent
                    item = unread_items[0]
                    item.click()
                    print("ECH0_FIVERR: Opened message thread.")

                    # Wait for chat to load
                    time.sleep(random.uniform(3, 5))

                    # EXTRACT MESSAGE TEXT
                    # Strategy: Try multiple potential selectors for robustness
                    last_message_text = ""
                    message_elements = []

                    # Potential selectors for message bubbles
                    selectors = [
                        ".message-content",
                        ".msg-body",
                        ".text-content",
                        ".message-text",
                        "div[class*='message-body']"
                    ]

                    for selector in selectors:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            message_elements = elements
                            break

                    if message_elements:
                        # Get text from the last message
                        # Ideally we want the last message from the partner, not us.
                        # This simple logic assumes the last message is from them (since it was unread)
                        last_message_text = message_elements[-1].text
                        print(f"ECH0_FIVERR: Read message: {last_message_text[:30]}...")
                    else:
                        print("ECH0_FIVERR: Could not locate message text with standard selectors.")
                        # Fallback: get page text just in case (risky, but better than crash)
                        # body_text = self.driver.find_element(By.TAG_NAME, "body").text

                    # GENERATE RESPONSE
                    if last_message_text:
                        response = llm_response_callback(last_message_text)
                        print(f"ECH0_FIVERR: Generated response: {response[:30]}...")

                        # TYPE AND SEND
                        # Try to find input box
                        input_box = None
                        input_selectors = [
                            "textarea[id*='message']",
                            "textarea.message-input",
                            "textarea",
                            "div[contenteditable='true']"
                        ]

                        for sel in input_selectors:
                            inputs = self.driver.find_elements(By.CSS_SELECTOR, sel)
                            if inputs:
                                # Pick the visible one
                                for inp in inputs:
                                    if inp.is_displayed():
                                        input_box = inp
                                        break
                                if input_box: break

                        if input_box:
                            # Mimic human typing?
                            input_box.click()
                            input_box.send_keys(response)
                            time.sleep(1)

                            # Find send button
                            send_btn = None
                            btn_selectors = [
                                "button[type='submit']",
                                ".send-button",
                                "button.send",
                                "button[class*='send']"
                            ]

                            for sel in btn_selectors:
                                btns = self.driver.find_elements(By.CSS_SELECTOR, sel)
                                if btns:
                                    for btn in btns:
                                        if btn.is_displayed():
                                            send_btn = btn
                                            break
                                    if send_btn: break

                            if send_btn:
                                send_btn.click()
                                print("ECH0_FIVERR: Response sent.")
                            else:
                                # Fallback: Enter key
                                input_box.send_keys(Keys.RETURN)
                                print("ECH0_FIVERR: Response sent via Enter key.")

                            processed_count += 1
                            time.sleep(3)
                        else:
                            print("ECH0_FIVERR: Could not find input box.")

                    # Return to inbox for next item
                    self.driver.get("https://www.fiverr.com/inbox")
                    time.sleep(3)

                except Exception as e:
                    print(f"ECH0_FIVERR: Error processing message: {e}")
                    # Attempt to recover by going back to inbox
                    self.driver.get("https://www.fiverr.com/inbox")
                    time.sleep(3)
                    break # Break to avoid infinite loops on error

        except Exception as e:
            print(f"ECH0_FIVERR: Auto-response cycle failed: {e}")

    def check_active_orders(self):
        """Checks for active orders requiring attention."""
        print("ECH0_FIVERR: Checking active orders...")
        try:
            self.driver.get("https://www.fiverr.com/users/orders")

            # Human-like page arrival
            if self.human:
                self.human.natural_page_arrival_behavior()
                # Sometimes scroll more to "look for orders"
                if random.random() < 0.4:
                    self.human.human_scroll("down", amount=random.randint(200, 400))
                    time.sleep(random.uniform(0.8, 1.5))
                    self.human.human_scroll("up", amount=random.randint(100, 250))
            else:
                time.sleep(random.uniform(2, 4))

            # Look for active order indicators
            active_orders = self.driver.find_elements(By.CSS_SELECTOR, ".order-item.active, .order-card")

            # Inefficient navigation - look at all orders, not just active
            if self.human and active_orders:
                all_orders = self.driver.find_elements(By.CSS_SELECTOR, "[class*='order']")
                if len(all_orders) > len(active_orders):
                    # Look at some non-active orders first (human behavior)
                    non_active = [o for o in all_orders if o not in active_orders][:3]
                    for order in non_active:
                        try:
                            self.human.human_move_to_element(order)
                            time.sleep(random.uniform(0.4, 0.9))
                        except:
                            pass

            if active_orders:
                count = len(active_orders)
                print(f"ECH0_FIVERR: {count} active order(s) detected.")
                return count
            else:
                print("ECH0_FIVERR: No active orders.")
                return 0
        except Exception as e:
            print(f"ECH0_FIVERR: Order check complete (no indicators): {e}")
            return 0

    def human_sleep(self):
        """Sleeps for a random interval to mimic biological irregularity."""
        sleep_time = random.uniform(45, 120)  # 45 to 120 seconds
        print(f"ECH0_FIVERR: Idling for {int(sleep_time)}s...")
        time.sleep(sleep_time)

    def shutdown(self):
        print("ECH0_FIVERR: Disengaging.")
        if hasattr(self, 'driver'):
            self.driver.quit()

# --- MAIN EXECUTION LOOP ---
if __name__ == "__main__":
    agent = FiverrAutonomousManager()

    if agent.connect_to_dashboard():
        try:
            print("ECH0_FIVERR: Engaging Autonomous Watchdog Mode (Ctrl+C to stop).")
            while True:
                agent.scan_inbox()
                # If we were running in full autonomous mode, we would call respond_to_unread_messages here
                # But for the standalone watchdog, we might just scan.
                # However, to test the new function, we could uncomment:
                # agent.respond_to_unread_messages(lambda x: "Auto-reply test")

                agent.check_active_orders()
                agent.human_sleep()
        except KeyboardInterrupt:
            print("\nECH0_FIVERR: Manual Override detected.")

    agent.shutdown()
