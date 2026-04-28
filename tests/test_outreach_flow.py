from unittest.mock import Mock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.blank_business_builder.agents.voice_agent import VoiceAgent
from src.blank_business_builder.database import Base, CallSession, LeadRecord, OutreachAttempt, ProviderEvent


class _FakeBland:
    def create_call(self, **kwargs):
        return {"call_id": "bland_call_1", "status": "queued", "request": kwargs}


class _FakeSlack:
    def __init__(self):
        self.messages = []

    def resolve_channel(self, department):
        return "C_SALES" if department == "sales" else None

    def post_message(self, channel_id, text):
        self.messages.append((channel_id, text))
        return {"ok": True}


class _FakeBrain:
    def decide_post_call_action(self, _payload):
        return {
            "next_action": "schedule_meeting",
            "follow_up_in_minutes": 30,
            "department": "sales",
            "slack_summary": "Interested lead, schedule demo",
        }


def test_full_outreach_flow(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    db = TestingSession()

    lead = LeadRecord(
        full_name="Alex Rivera",
        company="Acme",
        email="alex@acme.com",
        phone="+15555551212",
        status="new",
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    fake_slack = _FakeSlack()
    queued = []

    monkeypatch.setattr(
        "src.blank_business_builder.agents.voice_agent.IntegrationFactory.get_bland_service",
        Mock(return_value=_FakeBland()),
    )
    monkeypatch.setattr(
        "src.blank_business_builder.agents.voice_agent.IntegrationFactory.get_slack_service",
        Mock(return_value=fake_slack),
    )
    monkeypatch.setattr(
        "src.blank_business_builder.agents.voice_agent.EchoMasterBrain",
        Mock(return_value=_FakeBrain()),
    )
    monkeypatch.setattr(
        "src.blank_business_builder.agents.voice_agent.task_queue.add_task",
        lambda task_type, payload: queued.append((task_type, payload)),
    )

    voice = VoiceAgent()
    create_result = voice.create_outreach_call(
        db,
        lead=lead,
        webhook_url="https://bbb.test/api/webhooks/bland/post-call",
        department="sales",
        script="Use concise discovery questions",
        task="Call and qualify",
    )

    assert create_result["provider_call_id"] == "bland_call_1"
    attempt = db.query(OutreachAttempt).filter(OutreachAttempt.lead_id == lead.id).first()
    call = db.query(CallSession).filter(CallSession.provider_call_id == "bland_call_1").first()
    assert attempt is not None
    assert call is not None
    assert attempt.status == "in_progress"

    post_result = voice.handle_post_call_webhook(
        db,
        payload={
            "event": "post_call",
            "call_id": "bland_call_1",
            "status": "completed",
            "transcript": "They are interested and requested a demo.",
            "summary": "Strong fit",
            "outcome": "interested",
            "duration": 182,
            "metadata": {
                "lead_id": str(lead.id),
                "outreach_attempt_id": str(attempt.id),
                "department": "sales",
            },
        },
    )
    assert post_result["status"] == "processed"
    assert post_result["next_action"] == "schedule_meeting"

    db.refresh(attempt)
    db.refresh(call)
    db.refresh(lead)
    assert attempt.status == "completed"
    assert attempt.next_action == "schedule_meeting"
    assert call.status == "completed"
    assert call.summary == "Strong fit"
    assert lead.status == "called"
    assert lead.department == "sales"

    event = db.query(ProviderEvent).filter(ProviderEvent.external_id == "bland_call_1").first()
    assert event is not None
    assert event.processed is True
    assert queued and queued[0][0] == "voice_follow_up"
    assert fake_slack.messages == [("C_SALES", "Interested lead, schedule demo")]
