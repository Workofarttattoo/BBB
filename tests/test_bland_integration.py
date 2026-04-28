import hashlib
import hmac

from src.blank_business_builder.integrations.bland import BlandService


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.content = b"{}"

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeSession:
    def __init__(self):
        self.calls = []

    def request(self, **kwargs):
        self.calls.append(kwargs)
        return _FakeResponse({"ok": True, "id": "call_123"})


def test_bland_service_request_shapes():
    session = _FakeSession()
    service = BlandService(api_key="test-key", session=session)

    created = service.create_call(
        phone_number="+15555551212",
        task="Qualify and book demo",
        webhook="https://bbb.test/api/webhooks/bland/post-call",
        metadata={"lead_id": "lead_1"},
        pathway_id="pathway_1",
    )
    assert created["ok"] is True

    details = service.get_call("call_123")
    assert details["id"] == "call_123"

    listed = service.list_calls(limit=10, status="completed")
    assert listed["ok"] is True

    assert len(session.calls) == 3
    assert session.calls[0]["method"] == "POST"
    assert session.calls[0]["url"].endswith("/v1/calls")
    assert session.calls[1]["method"] == "GET"
    assert session.calls[1]["url"].endswith("/v1/calls/call_123")
    assert session.calls[2]["json"]["status"] == "completed"


def test_bland_webhook_signature_verification():
    secret = "bland-secret"
    payload = b'{"event":"post_call"}'
    expected_sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    service = BlandService(api_key="test-key", webhook_secret=secret)
    assert service.verify_webhook_signature(payload, expected_sig) is True
    assert service.verify_webhook_signature(payload, "bad") is False

    service_without_secret = BlandService(api_key="test-key", webhook_secret="")
    assert service_without_secret.verify_webhook_signature(payload, None) is True
