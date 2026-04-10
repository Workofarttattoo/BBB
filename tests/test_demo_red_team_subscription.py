import sys
import pytest
from unittest.mock import patch, MagicMock

# Mock sys.exit before importing the module because it calls sys.exit(1) on import failure
with patch("sys.exit"):
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'demos')))
    from demo_red_team_subscription import main

def test_main_keyboard_interrupt(capsys):
    """Test that main() handles KeyboardInterrupt properly."""

    # Run the main function, mock asyncio.run
    # the unraisable warning is from unittest.mock trying to be smart about async functions
    # Let's mock demo using a standard patch but ensure we close the coroutine if needed

    import asyncio

    async def dummy_coroutine():
        pass

    def mock_run(coro):
        coro.close() # Close to prevent warnings
        raise KeyboardInterrupt()

    with patch('demo_red_team_subscription.asyncio.run', side_effect=mock_run):
        main()

    captured = capsys.readouterr()
    assert "\nDemo interrupted.\n" in captured.out
