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
from selenium.webdriver.common.keys import Keys
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

# --- DOM SELECTORS (Verification Required) ---
# NOTE: These CSS selectors are estimates and must be verified/updated by Level 9 Vision AI
# or through manual inspection of the current Fiverr DOM structure.
UNREAD_MESSAGE_SELECTOR = ".unread"  # Selector for unread conversation in inbox list
MESSAGE_TEXT_SELECTOR = ".message-content:last-child"  # Selector for the last message bubble text
SENDER_NAME_SELECTOR = ".username, header h1, .contact-name"  # Selector for the sender's name
REPLY_INPUT_SELECTOR = "textarea[placeholder*='Type'], .message-composer textarea"  # Input box
SEND_BUTTON_SELECTOR = "button[type='submit'], .send-button"  # Send button

# --- ORDER SELECTORS ---
ORDER_ITEM_SELECTOR = ".order-item.active, .order-card"
ORDER_STATUS_SELECTOR = ".status-label, .status"
ORDER_BUYER_SELECTOR = ".buyer-name, .user-name"
ORDER_LINK_SELECTOR = "a[href*='/orders/']"
# Selector for message rows to determine sender
MESSAGE_ROW_SELECTOR = ".message-row, .message-wrapper"

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

    def process_unread_messages(self, llm_engine):
        """
        Process unread messages using LLM.
        Navigates to inbox, finds unread messages, and replies.
        """
        print("ECH0_FIVERR: Initiating intelligent message processing...")
        processed_count = 0

        # Max messages to process in one batch (human-like limit)
        MAX_BATCH = 3

        while processed_count < MAX_BATCH:
            try:
                # Navigate to inbox if not already there or to refresh list
                if "inbox" not in self.driver.current_url:
                    self.driver.get("https://www.fiverr.com/inbox")
                    time.sleep(random.uniform(3, 5))

                # Find unread messages AGAIN to avoid stale elements
                unread_msgs = self.driver.find_elements(By.CSS_SELECTOR, UNREAD_MESSAGE_SELECTOR)

                if not unread_msgs:
                    if processed_count == 0:
                        print("ECH0_FIVERR: No unread messages found to process.")
                    break

                # Always process the first one found, as the list order might change or elements become stale
                msg_element = unread_msgs[0]

                print(f"ECH0_FIVERR: Processing message {processed_count+1}")

                try:
                    # Open conversation
                    if self.human:
                        self.human.human_click(msg_element)
                    else:
                        msg_element.click()

                    time.sleep(random.uniform(3, 6)) # Wait for chat to load

                    # Extract information (Best Effort)
                    try:
                        # Find the last message text
                        msg_texts = self.driver.find_elements(By.CSS_SELECTOR, MESSAGE_TEXT_SELECTOR)
                        if msg_texts:
                            last_message = msg_texts[-1].text
                        else:
                            last_message = "(Could not read message content)"

                        # Find sender name
                        sender_elements = self.driver.find_elements(By.CSS_SELECTOR, SENDER_NAME_SELECTOR)
                        if sender_elements:
                            sender_name = sender_elements[0].text
                        else:
                            sender_name = "Client"

                        print(f"ECH0_FIVERR: From: {sender_name} | Message: {last_message[:50]}...")

                        # Generate response
                        response = llm_engine.generate_response(last_message, sender_name)

                        # Type response
                        input_box = self.driver.find_element(By.CSS_SELECTOR, REPLY_INPUT_SELECTOR)

                        if self.human:
                            self.human.human_type(input_box, response)
                        else:
                            input_box.send_keys(response)

                        time.sleep(random.uniform(1, 2))

                        # Send
                        send_btn = self.driver.find_element(By.CSS_SELECTOR, SEND_BUTTON_SELECTOR)
                        if self.human:
                            self.human.human_click(send_btn)
                        else:
                            send_btn.click()

                        print("ECH0_FIVERR: Response sent.")
                        processed_count += 1

                        # Return to inbox for next message
                        self.driver.get("https://www.fiverr.com/inbox")
                        time.sleep(random.uniform(2, 4))

                    except Exception as inner_e:
                        print(f"ECH0_FIVERR: [ERROR] Failed to process conversation: {inner_e}")
                        self.driver.back() # Try to go back to inbox
                        time.sleep(3)

                except Exception as e:
                    print(f"ECH0_FIVERR: [ERROR] Error clicking message: {e}")
                    # If we can't click the message, break to avoid infinite loop on same message
                    break

            except Exception as e:
                print(f"ECH0_FIVERR: [ERROR] Message processing loop failed: {e}")
                break

        return processed_count

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
            active_orders = self.driver.find_elements(By.CSS_SELECTOR, ORDER_ITEM_SELECTOR)

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

    def process_active_orders(self, llm_engine):
        """
        Process active orders using LLM.
        Navigates to orders page, finds active orders, and updates status/responds.
        """
        print("ECH0_FIVERR: processing active orders...")
        processed_stats = {"found": 0, "processed": 0}

        try:
            # Navigate to orders if not already there
            if "orders" not in self.driver.current_url:
                self.driver.get("https://www.fiverr.com/users/orders")
                time.sleep(random.uniform(2, 4))

            # Find active orders
            # Using find_elements to get a fresh list
            active_orders = self.driver.find_elements(By.CSS_SELECTOR, ORDER_ITEM_SELECTOR)
            processed_stats["found"] = len(active_orders)

            if not active_orders:
                print("ECH0_FIVERR: No active orders to process.")
                return processed_stats

            # Process each order
            # Note: DOM elements go stale after navigation, so we need to collect URLs first
            order_urls = []
            for order in active_orders:
                try:
                    link_elem = order.find_element(By.CSS_SELECTOR, ORDER_LINK_SELECTOR)
                    order_urls.append(link_elem.get_attribute("href"))
                except Exception:
                    continue

            print(f"ECH0_FIVERR: Found {len(order_urls)} order URLs to process.")

            for url in order_urls:
                try:
                    self.driver.get(url)
                    time.sleep(random.uniform(3, 5))

                    # Extract details
                    try:
                        buyer_name = self.driver.find_element(By.CSS_SELECTOR, ORDER_BUYER_SELECTOR).text
                    except:
                        buyer_name = "Client"

                    try:
                        status = self.driver.find_element(By.CSS_SELECTOR, ORDER_STATUS_SELECTOR).text
                    except:
                        status = "Unknown"

                    print(f"ECH0_FIVERR: Processing order for {buyer_name} (Status: {status})")

                    # Check for latest message
                    try:
                        msg_texts = self.driver.find_elements(By.CSS_SELECTOR, MESSAGE_TEXT_SELECTOR)
                        last_message = msg_texts[-1].text if msg_texts else ""

                        # Check if last message was from us to avoid infinite loops
                        last_message_from_me = False
                        try:
                            # Try to find message rows and check the last one
                            msg_rows = self.driver.find_elements(By.CSS_SELECTOR, MESSAGE_ROW_SELECTOR)
                            if msg_rows:
                                last_row = msg_rows[-1]
                                # Check if it has a class indicating it's mine (e.g. "me", "sent", "right")
                                class_attr = last_row.get_attribute("class")
                                if class_attr and ("me" in class_attr or "sent" in class_attr or "right" in class_attr):
                                    last_message_from_me = True
                        except Exception:
                            pass

                        # Fallback: check content if we can't determine by class
                        # If the last message contains our typical welcome phrase, assume it's us.
                        if "New order started" in last_message:
                             last_message_from_me = True

                        if last_message_from_me:
                            print(f"ECH0_FIVERR: Last message was from us. Skipping response for {buyer_name}.")
                            continue

                        # Determine if we need to respond
                        # Simplified: respond if status is "Incomplete" (New order)
                        if "Incomplete" in status or "New" in status:
                             print("ECH0_FIVERR: New order detected. Sending welcome message.")
                             response = llm_engine.generate_response(
                                 "New order started.",
                                 buyer_name,
                                 context={"type": "order_start", "status": status}
                             )

                             input_box = self.driver.find_element(By.CSS_SELECTOR, REPLY_INPUT_SELECTOR)
                             if self.human:
                                 self.human.human_type(input_box, response)
                             else:
                                 input_box.send_keys(response)

                             time.sleep(random.uniform(1, 2))

                             send_btn = self.driver.find_element(By.CSS_SELECTOR, SEND_BUTTON_SELECTOR)
                             if self.human:
                                 self.human.human_click(send_btn)
                             else:
                                 send_btn.click()

                             processed_stats["processed"] += 1
                             print("ECH0_FIVERR: Welcome message sent.")

                    except Exception as e:
                        print(f"ECH0_FIVERR: Error checking messages for order: {e}")

                except Exception as e:
                    print(f"ECH0_FIVERR: Failed to process order URL {url}: {e}")

        except Exception as e:
            print(f"ECH0_FIVERR: Error in process_active_orders: {e}")

        return processed_stats

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
                agent.check_active_orders()
                agent.human_sleep()
        except KeyboardInterrupt:
            print("\nECH0_FIVERR: Manual Override detected.")

    agent.shutdown()
