import sys
import unittest.mock

# Mock out duckduckgo_search since we don't have it installed
sys.modules['duckduckgo_search'] = unittest.mock.MagicMock()

import pytest
import subprocess
from src.blank_business_builder.autonomous_tools import AutonomousTools

def test_run_shell_command_list():
    from unittest.mock import patch
    with patch('subprocess.run') as mock_run:
        # Mock subprocess.run
        mock_run.return_value.stdout = "hello\n"
        mock_run.return_value.stderr = ""
        mock_run.return_value.returncode = 0

        tools = AutonomousTools()
        result = tools.run_shell_command(["echo", "hello"])

        # Assert subprocess.run was called correctly with shell=False
        mock_run.assert_called_once_with(
            ["echo", "hello"],
            shell=False,
            cwd=".",
            capture_output=True,
            text=True,
            timeout=60
        )
        assert result["stdout"] == "hello\n"
        assert result["returncode"] == 0

def test_run_shell_command_string():
    from unittest.mock import patch
    with patch('subprocess.run') as mock_run:
        # Mock subprocess.run
        mock_run.return_value.stdout = "hello world\n"
        mock_run.return_value.stderr = ""
        mock_run.return_value.returncode = 0

        tools = AutonomousTools()
        result = tools.run_shell_command("echo 'hello world'")

        # Assert subprocess.run was called correctly, and shlex parsed it
        mock_run.assert_called_once_with(
            ["echo", "hello world"],
            shell=False,
            cwd=".",
            capture_output=True,
            text=True,
            timeout=60
        )
        assert result["stdout"] == "hello world\n"
        assert result["returncode"] == 0
