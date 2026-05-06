"""
ElevenLabs text-to-speech integration for voice outreach assets.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import requests


class ElevenLabsService:
    """Thin API client for ElevenLabs text-to-speech generation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_voice_id: Optional[str] = None,
        default_model_id: Optional[str] = None,
        output_format: Optional[str] = None,
        timeout_seconds: int = 30,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY", "")
        self.base_url = (
            base_url or os.getenv("ELEVENLABS_BASE_URL", "https://api.elevenlabs.io")
        ).rstrip("/")
        self.default_voice_id = default_voice_id or os.getenv(
            "ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM"
        )
        self.default_model_id = default_model_id or os.getenv(
            "ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"
        )
        self.output_format = output_format or os.getenv(
            "ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128"
        )
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()

    def text_to_speech(
        self,
        text: str,
        *,
        voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
        output_format: Optional[str] = None,
        voice_settings: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """Generate audio bytes from text."""
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY is required")
        if not text.strip():
            raise ValueError("text is required")

        selected_voice = voice_id or self.default_voice_id
        selected_format = output_format or self.output_format
        payload: Dict[str, Any] = {
            "text": text,
            "model_id": model_id or self.default_model_id,
        }
        if voice_settings:
            payload["voice_settings"] = voice_settings

        response = self.session.post(
            url=f"{self.base_url}/v1/text-to-speech/{selected_voice}",
            params={"output_format": selected_format},
            json=payload,
            headers={
                "xi-api-key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return bytes(response.content)

    def write_speech_file(
        self,
        text: str,
        output_path: Union[str, Path],
        *,
        voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
        output_format: Optional[str] = None,
        voice_settings: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Generate speech and persist it to a local file."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        audio = self.text_to_speech(
            text,
            voice_id=voice_id,
            model_id=model_id,
            output_format=output_format,
            voice_settings=voice_settings,
        )
        path.write_bytes(audio)
        return path
