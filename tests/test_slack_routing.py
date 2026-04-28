import os

from src.blank_business_builder.hive_mind_coordinator import HiveMindCoordinator
from src.blank_business_builder.integrations.slack import SlackService


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeSession:
    def __init__(self):
        self.posts = []

    def post(self, url, json, headers, timeout):
        self.posts.append(
            {
                "url": url,
                "json": json,
                "headers": headers,
                "timeout": timeout,
            }
        )
        return _FakeResponse({"ok": True, "ts": "1710000000.000100"})


def test_slack_department_routing(monkeypatch):
    monkeypatch.setenv("SLACK_CHANNEL_SALES", "C_SALES")
    monkeypatch.setenv("SLACK_CHANNEL_MARKETING", "C_MKT")
    monkeypatch.setenv("SLACK_CHANNEL_OPS", "C_OPS")
    monkeypatch.setenv("SLACK_CHANNEL_EXEC", "C_EXEC")
    monkeypatch.setenv("SLACK_CHANNEL_SUPPORT", "C_SUPPORT")

    service = SlackService(bot_token="xoxb-test")
    assert service.resolve_channel("sales") == "C_SALES"
    assert service.resolve_channel("marketing") == "C_MKT"
    assert service.resolve_channel("ops") == "C_OPS"
    assert service.resolve_channel("exec") == "C_EXEC"
    assert service.resolve_channel("support") == "C_SUPPORT"
    assert service.resolve_channel("unknown") is None

    # Hive coordinator should resolve via same routing map.
    assert HiveMindCoordinator.resolve_department_channel_id("sales") == "C_SALES"
    assert HiveMindCoordinator.resolve_department_channel_id("exec") == "C_EXEC"


def test_slack_post_message_calls_chat_api():
    fake = _FakeSession()
    service = SlackService(bot_token="xoxb-test", session=fake)
    response = service.post_message("C_SALES", "New call summary")

    assert response["ok"] is True
    assert len(fake.posts) == 1
    assert fake.posts[0]["url"].endswith("/chat.postMessage")
    assert fake.posts[0]["json"]["channel"] == "C_SALES"
    assert fake.posts[0]["json"]["text"] == "New call summary"
    assert fake.posts[0]["headers"]["Authorization"] == "Bearer xoxb-test"
