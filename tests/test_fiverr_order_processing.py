import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock modules if not available
sys.modules['human_behavior_simulator'] = MagicMock()

# Import the class to test
# We need to set environment variables for the class to initialize
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

@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.generate_response.return_value = "Mock Response"
    return llm

def test_process_active_orders_no_orders(manager, mock_llm):
    # Setup
    manager.driver.current_url = "https://www.fiverr.com/users/orders"
    manager.driver.find_elements.return_value = [] # No active orders

    # Execute
    stats = manager.process_active_orders(mock_llm)

    # Verify
    assert stats['found'] == 0
    assert stats['processed'] == 0
    mock_llm.generate_response.assert_not_called()

def test_process_active_orders_with_new_order(manager, mock_llm):
    # Setup
    manager.driver.current_url = "https://www.fiverr.com/users/orders"

    # Mock active order element
    mock_order = MagicMock()
    mock_link = MagicMock()
    mock_link.get_attribute.return_value = "http://fiverr.com/order/123"
    mock_order.find_element.return_value = mock_link

    # Reset side_effect for find_elements to handle the sequence
    # 1. Main loop active orders
    # 2. Inside process_active_orders: message texts
    # 3. Inside process_active_orders: message rows (check for me)
    manager.driver.find_elements.side_effect = [
        [mock_order], # active_orders
        [], # msg_texts (empty)
        [], # msg_rows (empty)
    ]

    # Configure find_element return values
    mock_buyer = MagicMock()
    mock_buyer.text = "TestBuyer"

    mock_status = MagicMock()
    mock_status.text = "Incomplete" # Triggers response

    mock_input = MagicMock()
    mock_send = MagicMock()

    def find_element_side_effect(by, value):
        if "buyer" in value:
            return mock_buyer
        if "status" in value:
            return mock_status
        if "textarea" in value:
            return mock_input
        if "button" in value:
            return mock_send
        if "href" in value:
            return mock_link
        raise Exception(f"Unexpected selector: {value}")

    manager.driver.find_element.side_effect = find_element_side_effect

    # Execute
    stats = manager.process_active_orders(mock_llm)

    # Verify
    assert stats['found'] == 1
    assert stats['processed'] == 1
    mock_llm.generate_response.assert_called_once()

    # Check human behavior call
    manager.human.human_type.assert_called_with(mock_input, "Mock Response")
    manager.human.human_click.assert_called_with(mock_send)

def test_process_active_orders_existing_messages(manager, mock_llm):
    # Setup: Active order but status is "In Progress" (should not respond in simplified logic)

    manager.driver.current_url = "https://www.fiverr.com/users/orders"

    mock_order = MagicMock()
    mock_link = MagicMock()
    mock_link.get_attribute.return_value = "http://fiverr.com/order/123"
    mock_order.find_element.return_value = mock_link

    # 1. active_orders
    # 2. msg_texts
    # 3. msg_rows
    manager.driver.find_elements.side_effect = [
        [mock_order], # active_orders
        [MagicMock(text="Hello")], # msg_texts
        [MagicMock(get_attribute=MagicMock(return_value="message-row client"))], # msg_rows (client)
    ]

    mock_buyer = MagicMock(text="TestBuyer")
    mock_status = MagicMock(text="In Progress")

    def find_element_side_effect(by, value):
        if "buyer" in value:
            return mock_buyer
        if "status" in value:
            return mock_status
        if "href" in value:
            return mock_link
        # Should not call input/send if logic is correct
        raise Exception(f"Unexpected selector: {value}")

    manager.driver.find_element.side_effect = find_element_side_effect

    # Execute
    stats = manager.process_active_orders(mock_llm)

    # Verify
    assert stats['found'] == 1
    assert stats['processed'] == 0
    mock_llm.generate_response.assert_not_called()

def test_process_active_orders_already_responded(manager, mock_llm):
    # Setup: Active order, Incomplete status, BUT last message is from "me"

    manager.driver.current_url = "https://www.fiverr.com/users/orders"

    mock_order = MagicMock()
    mock_link = MagicMock()
    mock_link.get_attribute.return_value = "http://fiverr.com/order/123"
    mock_order.find_element.return_value = mock_link

    # Mock message row that is "me"
    mock_row = MagicMock()
    mock_row.get_attribute.return_value = "message-row me"

    # 1. active_orders
    # 2. msg_texts
    # 3. msg_rows
    manager.driver.find_elements.side_effect = [
        [mock_order], # active_orders
        [MagicMock(text="New order started.")], # msg_texts
        [mock_row], # msg_rows
    ]

    mock_buyer = MagicMock(text="TestBuyer")
    mock_status = MagicMock(text="Incomplete")

    def find_element_side_effect(by, value):
        if "buyer" in value: return mock_buyer
        if "status" in value: return mock_status
        if "href" in value: return mock_link
        raise Exception(f"Unexpected selector: {value}")
    manager.driver.find_element.side_effect = find_element_side_effect

    # Execute
    stats = manager.process_active_orders(mock_llm)

    # Verify
    assert stats['found'] == 1
    assert stats['processed'] == 0
    mock_llm.generate_response.assert_not_called()
