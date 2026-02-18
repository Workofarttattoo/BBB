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
ORDER_GIG_TITLE_SELECTOR = ".gig-title, .order-title, h1 a, h2 a, .order-gig-title"
# Selector for message rows to determine sender
MESSAGE_ROW_SELECTOR = ".message-row, .message-wrapper"
# Selector for message content
MESSAGE_TEXT_SELECTOR = ".message-content, .msg-body"

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

    def get_active_orders_details(self):
        """
        Get details of all active orders requiring attention.
        Returns a list of dictionaries with order details.
        Does NOT perform actions (side-effect free except navigation).
        """
        print("ECH0_FIVERR: Scanning for active orders requiring attention...")
        orders_requiring_attention = []

        try:
            # Always navigate to orders list to ensure we are not stuck on a detail page
            # Check if we are already on the list page to save a reload
            if self.driver.current_url != "https://www.fiverr.com/users/orders":
                 self.driver.get("https://www.fiverr.com/users/orders")
                 time.sleep(random.uniform(2, 4))

            # Find active orders
            active_orders = self.driver.find_elements(By.CSS_SELECTOR, ORDER_ITEM_SELECTOR)

            if not active_orders:
                print("ECH0_FIVERR: No active orders found.")
                return []

            # Collect URLs first to avoid stale element reference
            order_urls = []
            for order in active_orders:
                try:
                    link_elem = order.find_element(By.CSS_SELECTOR, ORDER_LINK_SELECTOR)
                    order_urls.append(link_elem.get_attribute("href"))
                except Exception:
                    continue

            print(f"ECH0_FIVERR: Inspecting {len(order_urls)} active orders...")

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

                    try:
                        gig_title = self.driver.find_element(By.CSS_SELECTOR, ORDER_GIG_TITLE_SELECTOR).text
                    except:
                        gig_title = "Unknown Gig"

                    print(f"ECH0_FIVERR: Order [{status}] for '{gig_title}' from {buyer_name}")

                    # Check for latest message
                    msg_texts = self.driver.find_elements(By.CSS_SELECTOR, MESSAGE_TEXT_SELECTOR)
                    last_message = msg_texts[-1].text if msg_texts else ""

                    # Check if last message was from us
                    last_message_from_me = False
                    try:
                        msg_rows = self.driver.find_elements(By.CSS_SELECTOR, MESSAGE_ROW_SELECTOR)
                        if msg_rows:
                            last_row = msg_rows[-1]
                            class_attr = last_row.get_attribute("class")
                            if class_attr and ("me" in class_attr or "sent" in class_attr or "right" in class_attr):
                                last_message_from_me = True
                    except Exception:
                        pass

                    # If "New order started" or "Order in progress" is the last message text,
                    # it means no human (us or them) has spoken yet.
                    # In this case, we treat it as "needs attention" (we need to send welcome message).
                    # So we DON'T set last_message_from_me = True for system messages.
                    is_system_message = "New order started" in last_message or "Order in progress" in last_message

                    # Logic to determine if attention is needed
                    needs_attention = False

                    if "Incomplete" in status or "New" in status:
                        # Respond if we haven't spoken yet (even if it's just a system message)
                        needs_attention = not last_message_from_me
                    elif "In Progress" in status:
                        # Respond if the client spoke last
                        # If the last message is a system message "Order in progress", we might want to greet if we haven't already.
                        # But safely, let's only respond if client explicitly spoke or if we assume we must welcome them.
                        if is_system_message:
                             # We haven't welcomed them to the "In Progress" stage yet?
                             # Risk: we might loop if we don't send a message that clears "is_system_message" condition.
                             # But sending a message puts OUR message last, so last_message_from_me becomes True.
                             needs_attention = True
                        else:
                             needs_attention = not last_message_from_me

                    if needs_attention:
                        print(f"ECH0_FIVERR: >> Needs Attention: {buyer_name}")
                        orders_requiring_attention.append({
                            "url": url,
                            "buyer": buyer_name,
                            "status": status,
                            "gig_title": gig_title,
                            "last_message": last_message
                        })

                except Exception as e:
                    print(f"ECH0_FIVERR: Failed to inspect order URL {url}: {e}")

        except Exception as e:
            print(f"ECH0_FIVERR: Error in get_active_orders_details: {e}")

        return orders_requiring_attention

    def send_reply(self, order_url: str, message_text: str):
        """
        Send a reply to a specific order.
        """
        print(f"ECH0_FIVERR: Sending reply to {order_url}...")
        try:
            if self.driver.current_url != order_url:
                self.driver.get(order_url)
                time.sleep(random.uniform(2, 4))

            input_box = self.driver.find_element(By.CSS_SELECTOR, REPLY_INPUT_SELECTOR)
            if self.human:
                self.human.human_type(input_box, message_text)
            else:
                input_box.send_keys(message_text)

            time.sleep(random.uniform(1, 2))

            send_btn = self.driver.find_element(By.CSS_SELECTOR, SEND_BUTTON_SELECTOR)
            if self.human:
                self.human.human_click(send_btn)
            else:
                send_btn.click()

            print("ECH0_FIVERR: Reply sent successfully.")
            return True

        except Exception as e:
            print(f"ECH0_FIVERR: Failed to send reply: {e}")
            return False

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
