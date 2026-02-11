import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock modules if not available
sys.modules['human_behavior_simulator'] = MagicMock()

# Import the class to test
os.environ['FIVERR_CHROME_PROFILE_PATH'] = '/tmp/fake_profile'
os.environ['FIVERR_PROFILE_DIRECTORY'] = 'Default'

from fiverr_autonomous_manager import FiverrAutonomousManager

@pytest.fixture
def mock_driver():
    with patch('fiverr_autonomous_manager.webdriver.Chrome') as mock:
        driver = mock.return_value
        yield driver

@pytest.fixture
def manager(mock_driver):
    return FiverrAutonomousManager()

def test_get_active_orders_details_no_orders(manager):
    # Setup
    manager.driver.current_url = "https://www.fiverr.com/users/orders"
    manager.driver.find_elements.return_value = [] # No active orders

    # Execute
    orders = manager.get_active_orders_details()

    # Verify
    assert orders == []

def test_get_active_orders_details_with_new_order(manager):
    # Setup
    # Simulate being on a different page initially, forcing navigation
    manager.driver.current_url = "https://www.fiverr.com/some/other/page"

    # Mock active order element
    mock_order = MagicMock()
    mock_link = MagicMock()
    mock_link.get_attribute.return_value = "http://fiverr.com/order/123"
    mock_order.find_element.return_value = mock_link

    # Reset side_effect for find_elements to handle the sequence
    # 1. Main loop active orders
    # 2. Inside loop: message texts
    # 3. Inside loop: message rows
    manager.driver.find_elements.side_effect = [
        [mock_order], # active_orders
        [MagicMock(text="New order started")], # msg_texts (System message)
        [], # msg_rows (empty, so not from me)
    ]

    # Configure find_element return values
    mock_buyer = MagicMock(text="TestBuyer")
    mock_status = MagicMock(text="Incomplete") # Triggers needs_attention
    mock_gig_title = MagicMock(text="AI Chatbot Service")

    def find_element_side_effect(by, value):
        if "buyer" in value: return mock_buyer
        if "status" in value: return mock_status
        if "gig-title" in value or "order-title" in value: return mock_gig_title
        if "href" in value: return mock_link
        raise Exception(f"Unexpected selector: {value}")

    manager.driver.find_element.side_effect = find_element_side_effect

    # Execute
    orders = manager.get_active_orders_details()

    # Verify navigation occurred
    manager.driver.get.assert_any_call("https://www.fiverr.com/users/orders")

    # Verify order details
    assert len(orders) == 1
    order = orders[0]
    assert order['buyer'] == "TestBuyer"
    assert order['status'] == "Incomplete"
    assert order['gig_title'] == "AI Chatbot Service"
    assert order['url'] == "http://fiverr.com/order/123"

def test_get_active_orders_details_already_responded(manager):
    # Setup: Active order, Incomplete status, BUT last message is from "me"

    manager.driver.current_url = "https://www.fiverr.com/users/orders"
    mock_order = MagicMock()
    mock_link = MagicMock(get_attribute=MagicMock(return_value="http://fiverr.com/order/123"))
    mock_order.find_element.return_value = mock_link

    # Mock message row that is "me"
    mock_row = MagicMock()
    mock_row.get_attribute.return_value = "message-row me"

    manager.driver.find_elements.side_effect = [
        [mock_order], # active_orders
        [MagicMock(text="New order started.")], # msg_texts (text doesn't matter much if row says ME)
        [mock_row], # msg_rows
    ]

    mock_buyer = MagicMock(text="TestBuyer")
    mock_status = MagicMock(text="Incomplete")
    mock_gig_title = MagicMock(text="AI Chatbot Service")

    def find_element_side_effect(by, value):
        if "buyer" in value: return mock_buyer
        if "status" in value: return mock_status
        if "gig-title" in value: return mock_gig_title
        if "href" in value: return mock_link
        raise Exception(f"Unexpected selector: {value}")
    manager.driver.find_element.side_effect = find_element_side_effect

    # Execute
    orders = manager.get_active_orders_details()

    # Verify: Should be empty because it doesn't need attention
    assert len(orders) == 0

def test_send_reply(manager):
    mock_input = MagicMock()
    mock_send = MagicMock()

    def find_element_side_effect(by, value):
        if "textarea" in value: return mock_input
        if "button" in value: return mock_send
        return MagicMock()

    manager.driver.find_element.side_effect = find_element_side_effect

    # Execute
    success = manager.send_reply("http://fiverr.com/order/123", "Hello World")

    # Verify
    assert success is True
    # Human behavior calls
    manager.human.human_type.assert_called_with(mock_input, "Hello World")
    manager.human.human_click.assert_called_with(mock_send)
