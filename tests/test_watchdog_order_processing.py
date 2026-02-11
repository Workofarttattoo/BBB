
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock the missing dependencies
sys.modules['selenium'] = MagicMock()
sys.modules['selenium.webdriver'] = MagicMock()
sys.modules['selenium.webdriver.chrome.service'] = MagicMock()
sys.modules['selenium.webdriver.chrome.options'] = MagicMock()
sys.modules['selenium.webdriver.common.by'] = MagicMock()
sys.modules['selenium.webdriver.support.ui'] = MagicMock()
sys.modules['selenium.webdriver.support'] = MagicMock()
sys.modules['webdriver_manager'] = MagicMock()
sys.modules['webdriver_manager.chrome'] = MagicMock()

# Now we can import the actual modules because their dependencies are mocked
sys.path.append(os.getcwd())

# However, importing fiverr_autonomous_manager will still try to run the top-level code.
# Ideally we want to test the logic in FiverrWatchdog without depending on the environment.

from fiverr_watchdog_autonomous import FiverrWatchdog

class TestWatchdogOrderProcessing(unittest.TestCase):
    def setUp(self):
        # Mock the log path to avoid creating real files
        self.watchdog = FiverrWatchdog(log_path="/tmp/test_fiverr_watchdog.log")
        self.watchdog.agent = MagicMock()

        # Capture logs
        self.logs = []
        def mock_log(category, message):
            self.logs.append(f"[{category}] {message}")

        self.watchdog.log = mock_log

    def test_process_orders(self):
        orders = [
            {"id": "123", "text_summary": "Logo Design", "link": "http://fiverr.com/order/123"},
            {"id": "456", "text_summary": "Website Dev", "link": "http://fiverr.com/order/456"}
        ]

        self.watchdog.process_orders(orders)

        self.assertIn("[ORDERS] Processing 2 active orders...", self.logs)
        self.assertIn("[ORDER_PROC] Processing Order #123: Logo Design", self.logs)
        self.assertIn("[ORDER_PROC] Processing Order #456: Website Dev", self.logs)
        self.assertIn("[ORDERS] Order processing cycle complete.", self.logs)

    def test_check_fiverr_activity_with_orders(self):
        # Mock agent responses
        self.watchdog.agent.connect_to_dashboard.return_value = True
        self.watchdog.agent.scan_inbox.return_value = 0

        # Mock get_active_order_details to return orders
        self.watchdog.agent.get_active_order_details.return_value = [
            {"id": "999", "text_summary": "Urgent Fix", "link": "http://fiverr.com/order/999"}
        ]

        # Run check cycle
        # We need to mock time.sleep to avoid waiting
        with patch('time.sleep'):
            self.watchdog.check_fiverr_activity()

        # Verify
        self.assertIn("[ORDERS] Found 1 active order(s)", self.logs)
        self.assertIn("[ORDERS] Processing 1 active orders...", self.logs)
        self.assertIn("[ORDER_PROC] Processing Order #999: Urgent Fix", self.logs)
        self.assertEqual(self.watchdog.stats["orders_found"], 1)

    def test_check_fiverr_activity_no_orders(self):
        # Mock agent responses
        self.watchdog.agent.connect_to_dashboard.return_value = True
        self.watchdog.agent.scan_inbox.return_value = 0
        self.watchdog.agent.get_active_order_details.return_value = []

        with patch('time.sleep'):
            self.watchdog.check_fiverr_activity()

        self.assertIn("[ORDERS] No active orders", self.logs)
        self.assertEqual(self.watchdog.stats["orders_found"], 0)

if __name__ == '__main__':
    unittest.main()
