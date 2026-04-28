from src.blank_business_builder.echo_master_brain import EchoMasterBrain


class _Response:
    content = b'{"status": "healthy"}'

    def __init__(self, payload=None):
        self._payload = payload or {"status": "healthy"}

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _Session:
    def __init__(self, *, get_response=None, post_responses=None):
        self.get_response = get_response or _Response()
        self.post_responses = post_responses or []
        self.get_calls = []
        self.post_calls = []

    def get(self, url, **kwargs):
        self.get_calls.append((url, kwargs))
        return self.get_response

    def post(self, url, **kwargs):
        self.post_calls.append((url, kwargs))
        if self.post_responses:
            return self.post_responses.pop(0)
        return _Response({})


def test_health_reports_unconfigured_fallback():
    brain = EchoMasterBrain(base_url="")

    assert brain.health() == {
        "configured": False,
        "connected": False,
        "base_url": "",
        "status": "fallback",
    }


def test_health_checks_configured_echo_prime_service():
    session = _Session(get_response=_Response({"status": "healthy", "service": "echo_prime"}))
    brain = EchoMasterBrain(base_url="http://echo-prime:8001", session=session)

    health = brain.health()

    assert health["configured"] is True
    assert health["connected"] is True
    assert health["base_url"] == "http://echo-prime:8001"
    assert health["status"] == "healthy"
    assert session.get_calls[0][0] == "http://echo-prime:8001/health"


def test_decide_outreach_uses_echo_prime_before_fallback():
    decision = {
        "department": "exec",
        "outreach_priority": 95,
        "should_call": True,
        "task": "Call with board-level value framing.",
        "script": "Ask about strategic priorities.",
    }
    session = _Session(post_responses=[_Response(decision)])
    brain = EchoMasterBrain(base_url="http://echo-prime:8001", session=session)

    result = brain.decide_outreach({"full_name": "Alex", "company": "Acme", "phone": "+1555"})

    assert result == decision
    assert session.post_calls[0][0] == "http://echo-prime:8001/internal/echo/outreach-decision"
