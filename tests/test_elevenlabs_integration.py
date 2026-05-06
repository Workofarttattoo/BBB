from pathlib import Path
from unittest.mock import Mock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.blank_business_builder.agents.voice_agent import VoiceAgent
from src.blank_business_builder.database import Base, LeadRecord, OutreachAttempt, ProviderEvent
from src.blank_business_builder.integrations.elevenlabs import ElevenLabsService


class _FakeResponse:
    content = b"audio-bytes"

    def raise_for_status(self):
        return None


class _FakeSession:
    def __init__(self):
        self.posts = []

    def post(self, url, params, json, headers, timeout):
        self.posts.append(
            {
                "url": url,
                "params": params,
                "json": json,
                "headers": headers,
                "timeout": timeout,
            }
        )
        return _FakeResponse()


class _FakeElevenLabs:
    def __init__(self):
        self.calls = []

    def write_speech_file(self, text, output_path, voice_id=None, model_id=None):
        self.calls.append(
            {
                "text": text,
                "output_path": Path(output_path),
                "voice_id": voice_id,
                "model_id": model_id,
            }
        )
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"audio-bytes")
        return Path(output_path)


class _FakeBland:
    pass


class _FakeSlack:
    pass


def test_elevenlabs_text_to_speech_posts_expected_payload():
    session = _FakeSession()
    service = ElevenLabsService(
        api_key="eleven-key",
        default_voice_id="voice-123",
        default_model_id="model-123",
        session=session,
    )

    audio = service.text_to_speech("Hello Alex")

    assert audio == b"audio-bytes"
    assert len(session.posts) == 1
    post = session.posts[0]
    assert post["url"].endswith("/v1/text-to-speech/voice-123")
    assert post["params"] == {"output_format": "mp3_44100_128"}
    assert post["json"] == {"text": "Hello Alex", "model_id": "model-123"}
    assert post["headers"]["xi-api-key"] == "eleven-key"


def test_voice_agent_creates_elevenlabs_outreach_asset(monkeypatch, tmp_path):
    engine = create_engine("sqlite:///:memory:")
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    db = TestingSession()

    lead = LeadRecord(
        full_name="Alex Rivera",
        company="Acme",
        email="alex@acme.com",
        status="new",
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    fake_elevenlabs = _FakeElevenLabs()
    monkeypatch.setattr(
        "src.blank_business_builder.agents.voice_agent.IntegrationFactory.get_bland_service",
        Mock(return_value=_FakeBland()),
    )
    monkeypatch.setattr(
        "src.blank_business_builder.agents.voice_agent.IntegrationFactory.get_elevenlabs_service",
        Mock(return_value=fake_elevenlabs),
    )
    monkeypatch.setattr(
        "src.blank_business_builder.agents.voice_agent.IntegrationFactory.get_slack_service",
        Mock(return_value=_FakeSlack()),
    )

    voice = VoiceAgent()
    result = voice.create_elevenlabs_outreach_audio(
        db,
        lead=lead,
        script="Hi Alex, this is a short B2B follow-up.",
        voice_id="voice-456",
        model_id="model-456",
        output_dir=str(tmp_path),
    )

    assert result["provider"] == "elevenlabs"
    assert result["status"] == "completed"
    assert Path(result["audio_path"]).exists()
    assert fake_elevenlabs.calls[0]["voice_id"] == "voice-456"

    attempt = db.query(OutreachAttempt).filter(OutreachAttempt.lead_id == lead.id).one()
    event = db.query(ProviderEvent).filter(ProviderEvent.provider == "elevenlabs").one()
    db.refresh(lead)
    assert attempt.channel == "voice_asset"
    assert attempt.status == "completed"
    assert event.processed is True
    assert lead.status == "voice_asset_ready"
