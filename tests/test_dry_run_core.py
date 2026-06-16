import sys
import os
import asyncio
from unittest.mock import patch, MagicMock

# Add necessary paths to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts/ech0')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts/tools')))

from dry_run_core import dry_run

def test_dry_run_success(capsys):
    """
    Test that dry_run initializes ECH0AutonomousCore and prints expected status.
    Uses capsys to capture stdout and verifies the output.
    """
    # Mock ECH0AutonomousCore
    with patch('dry_run_core.ECH0AutonomousCore') as mock_core_cls:
        # Configure mock instance
        mock_instance = MagicMock()
        mock_instance.system_status = "ONLINE"
        mock_instance.modules = {'email': MagicMock(), 'social': MagicMock()}
        mock_instance.activity_log = [
            {'module': 'core', 'action': 'start', 'details': 'System initialized'},
            {'module': 'email', 'action': 'init', 'details': 'Email ready'}
        ]

        # Configure the email module mock
        mock_email = mock_instance.modules['email']
        mock_email.send_email.return_value = True

        mock_core_cls.return_value = mock_instance

        # Run the async function
        asyncio.run(dry_run())

        # Capture output
        captured = capsys.readouterr()
        stdout = captured.out

        # Verify calls
        mock_core_cls.assert_called_once()
        mock_email.send_email.assert_called_once_with(
            to="inventor@aios.is",
            subject="DRY RUN REPORT",
            body="This is a system dry run test."
        )

        # Verify output
        assert "🚀 Starting ECH0 Autonomous Core DRY RUN..." in stdout
        assert "System Status: ONLINE" in stdout
        assert "Loaded Modules: ['email', 'social']" in stdout
        assert "Testing Module Communication Handlers" in stdout
        assert "Sent output: True" in stdout
        assert "Activity Log (Last 5)" in stdout
        assert "[core - start] System initialized" in stdout
        assert "✅ Dry run complete. Modules initialized correctly." in stdout

def test_dry_run_no_email_module(capsys):
    """
    Test dry_run behavior when the email module is not loaded.
    """
    with patch('dry_run_core.ECH0AutonomousCore') as mock_core_cls:
        # Configure mock instance without email module
        mock_instance = MagicMock()
        mock_instance.system_status = "DEGRADED"
        mock_instance.modules = {'social': MagicMock()}
        mock_instance.activity_log = []

        mock_core_cls.return_value = mock_instance

        # Run the async function
        asyncio.run(dry_run())

        # Capture output
        captured = capsys.readouterr()
        stdout = captured.out

        # Verify calls
        mock_core_cls.assert_called_once()

        # Verify output
        assert "🚀 Starting ECH0 Autonomous Core DRY RUN..." in stdout
        assert "System Status: DEGRADED" in stdout
        assert "Loaded Modules: ['social']" in stdout
        assert "Testing Module Communication Handlers" not in stdout
        assert "✅ Dry run complete. Modules initialized correctly." in stdout
