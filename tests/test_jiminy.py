import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import logging
from src.blank_business_builder.jiminy import (
    JiminyCricket,
    ConscienceConfig,
    create_jiminy,
    check_license_file,
    DEFAULT_REMINDERS
)

class TestJiminyCricket:
    """Tests for the JiminyCricket class and related functions."""

    def test_initialization_default(self):
        """Test JiminyCricket with default configuration."""
        jiminy = JiminyCricket()
        assert jiminy.config.enabled is True
        assert jiminy.config.reminders == DEFAULT_REMINDERS
        assert jiminy.config.checks == []
        assert jiminy.config.logger.name == "jiminy_cricket"
        assert jiminy.config.logger.level == logging.INFO
        assert len(jiminy.config.logger.handlers) > 0

    def test_initialization_custom(self):
        """Test JiminyCricket with custom configuration."""
        mock_logger = MagicMock(spec=logging.Logger)
        mock_logger.handlers = [MagicMock()]
        custom_checks = [lambda: True]
        custom_reminders = ["Don't be evil."]

        config = ConscienceConfig(
            enabled=False,
            checks=custom_checks,
            reminders=custom_reminders,
            logger=mock_logger
        )
        jiminy = JiminyCricket(config=config)

        assert jiminy.config.enabled is False
        assert jiminy.config.checks == custom_checks
        assert jiminy.config.reminders == custom_reminders
        assert jiminy.config.logger == mock_logger

    def test_affirm_enabled(self):
        """Test affirm logs when enabled."""
        mock_logger = MagicMock(spec=logging.Logger)
        mock_logger.handlers = [MagicMock()]
        jiminy = JiminyCricket(config=ConscienceConfig(logger=mock_logger, enabled=True))

        jiminy.affirm("Positive vibes")
        mock_logger.info.assert_called_once_with("Positive vibes")

    def test_affirm_disabled(self):
        """Test affirm does not log when disabled."""
        mock_logger = MagicMock(spec=logging.Logger)
        mock_logger.handlers = [MagicMock()]
        jiminy = JiminyCricket(config=ConscienceConfig(logger=mock_logger, enabled=False))

        jiminy.affirm("Should not log")
        mock_logger.info.assert_not_called()

    def test_run_checks_success(self):
        """Test run_checks when all checks pass."""
        mock_logger = MagicMock(spec=logging.Logger)
        mock_logger.handlers = [MagicMock()]
        check1 = MagicMock(return_value=True)
        check1.__name__ = "check1"
        check2 = MagicMock(return_value=True)
        check2.__name__ = "check2"

        jiminy = JiminyCricket(config=ConscienceConfig(logger=mock_logger, checks=[check1, check2]))

        assert jiminy.run_checks() is True
        mock_logger.info.assert_called_with("All Jiminy checks passed.")

    def test_run_checks_failure(self):
        """Test run_checks when some checks fail."""
        mock_logger = MagicMock(spec=logging.Logger)
        mock_logger.handlers = [MagicMock()]
        check1 = MagicMock(return_value=True)
        check1.__name__ = "check1"
        check2 = MagicMock(return_value=False)
        check2.__name__ = "check2"

        jiminy = JiminyCricket(config=ConscienceConfig(logger=mock_logger, checks=[check1, check2]))

        assert jiminy.run_checks() is False
        mock_logger.warning.assert_called_once()
        assert "check2" in mock_logger.warning.call_args[0][1]

    def test_run_checks_exception(self):
        """Test run_checks when a check raises an exception."""
        mock_logger = MagicMock(spec=logging.Logger)
        mock_logger.handlers = [MagicMock()]
        check1 = MagicMock(side_effect=Exception("Crashed!"))
        check1.__name__ = "check1"

        jiminy = JiminyCricket(config=ConscienceConfig(logger=mock_logger, checks=[check1]))

        assert jiminy.run_checks() is False
        mock_logger.error.assert_called_once()
        assert "check1" in mock_logger.error.call_args[0][1]
        assert "Crashed!" in str(mock_logger.error.call_args[0][2])

    def test_run_checks_disabled(self):
        """Test run_checks returns True without running checks when disabled."""
        mock_logger = MagicMock(spec=logging.Logger)
        mock_logger.handlers = [MagicMock()]
        check1 = MagicMock()

        jiminy = JiminyCricket(config=ConscienceConfig(logger=mock_logger, checks=[check1], enabled=False))

        assert jiminy.run_checks() is True
        check1.assert_not_called()

    def test_remind_enabled(self):
        """Test remind logs all reminders when enabled."""
        mock_logger = MagicMock(spec=logging.Logger)
        mock_logger.handlers = [MagicMock()]
        reminders = ["R1", "R2"]
        jiminy = JiminyCricket(config=ConscienceConfig(logger=mock_logger, reminders=reminders, enabled=True))

        jiminy.remind()
        assert mock_logger.info.call_count == 2
        mock_logger.info.assert_any_call("Reminder: %s", "R1")
        mock_logger.info.assert_any_call("Reminder: %s", "R2")

    def test_remind_disabled(self):
        """Test remind does not log when disabled."""
        mock_logger = MagicMock(spec=logging.Logger)
        mock_logger.handlers = [MagicMock()]
        jiminy = JiminyCricket(config=ConscienceConfig(logger=mock_logger, enabled=False))

        jiminy.remind()
        mock_logger.info.assert_not_called()

    def test_conscience_context_manager(self):
        """Test conscience context manager logs start, end, and calls remind."""
        mock_logger = MagicMock(spec=logging.Logger)
        mock_logger.handlers = [MagicMock()]
        jiminy = JiminyCricket(config=ConscienceConfig(logger=mock_logger, enabled=True))
        jiminy.remind = MagicMock()

        with jiminy.conscience("TestTask"):
            pass

        mock_logger.info.assert_any_call("Beginning %s with Jiminy oversight", "TestTask")
        # Second call is "Completed TestTask in ...s"
        assert any(call[0][0] == "Completed %s in %.2fs" and call[0][1] == "TestTask"
                   for call in mock_logger.info.call_args_list)
        jiminy.remind.assert_called_once()

    def test_create_jiminy_helper(self):
        """Test create_jiminy helper function."""
        checks = [lambda: True]
        reminders = ["Be kind."]
        jiminy = create_jiminy(enabled=True, checks=checks, reminders=reminders)

        assert isinstance(jiminy, JiminyCricket)
        assert jiminy.config.enabled is True
        assert jiminy.config.checks == checks
        assert jiminy.config.reminders == reminders

    def test_check_license_file_helper(self):
        """Test check_license_file helper returns correct callable."""
        mock_path = MagicMock(spec=Path)
        mock_path.name = "LICENSE"
        mock_path.exists.return_value = True

        check_func = check_license_file(mock_path)
        assert check_func.__name__ == "check_license_file_LICENSE"
        assert check_func() is True
        mock_path.exists.assert_called_once()

        mock_path.exists.return_value = False
        assert check_func() is False
