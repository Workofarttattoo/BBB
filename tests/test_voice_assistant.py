import pytest
import asyncio
from src.blank_business_builder.all_features_implementation import VoiceAssistant, VoiceCommand

class TestVoiceAssistant:
    """Tests for the VoiceAssistant class."""

    @pytest.mark.asyncio
    async def test_process_voice_command_get_metrics(self):
        """Test that process_voice_command returns metrics (default behavior)."""
        assistant = VoiceAssistant()
        # Input audio data is ignored in the current implementation
        result = await assistant.process_voice_command("dummy audio data")

        assert "response" in result
        assert "Your revenue this month is $125,000" in result["response"]
        assert "data" in result
        assert result["data"]["revenue"] == 125000
        assert result["data"]["users"] == 450

    @pytest.mark.asyncio
    async def test_execute_command_get_metrics(self):
        """Test _execute_command explicitly with GET_METRICS."""
        assistant = VoiceAssistant()
        result = await assistant._execute_command(VoiceCommand.GET_METRICS, {})

        assert "response" in result
        assert "Your revenue this month is $125,000" in result["response"]
        assert "data" in result
        assert result["data"]["revenue"] == 125000
        assert result["data"]["users"] == 450

    @pytest.mark.asyncio
    async def test_execute_command_other(self):
        """Test _execute_command with other commands."""
        assistant = VoiceAssistant()

        # Test CREATE_CAMPAIGN
        result = await assistant._execute_command(VoiceCommand.CREATE_CAMPAIGN, {})
        assert result == {"response": "Command executed successfully"}

        # Test SCHEDULE_MEETING
        result = await assistant._execute_command(VoiceCommand.SCHEDULE_MEETING, {})
        assert result == {"response": "Command executed successfully"}

        # Test SEND_EMAIL
        result = await assistant._execute_command(VoiceCommand.SEND_EMAIL, {})
        assert result == {"response": "Command executed successfully"}
