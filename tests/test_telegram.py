from __future__ import annotations

import httpx

from app.config import get_settings
from app.schemas.ai_result import AIResult
from app.schemas.lead import LeadIn


class _FakeResponse:
    status_code = 200

    def raise_for_status(self) -> None:
        return None


def test_send_message_posts_to_bot_api(monkeypatch):
    monkeypatch.setenv("TELEGRAM_ENABLED", "true")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    get_settings.cache_clear()

    calls = []

    def fake_post(url, json, timeout):
        calls.append({"url": url, "json": json, "timeout": timeout})
        return _FakeResponse()

    monkeypatch.setattr(httpx, "post", fake_post)
    try:
        from app.services.telegram import send_message

        result = send_message("hello")

        assert result is True
        assert len(calls) == 1
        assert calls[0]["url"].endswith("/sendMessage")
        assert "test-token" in calls[0]["url"]
        assert calls[0]["json"]["chat_id"] == "12345"
        assert calls[0]["json"]["text"] == "hello"
    finally:
        get_settings.cache_clear()


def test_send_message_disabled_skips_network(monkeypatch):
    monkeypatch.setenv("TELEGRAM_ENABLED", "false")
    get_settings.cache_clear()

    calls = []

    def fake_post(url, json, timeout):
        calls.append(url)
        return _FakeResponse()

    monkeypatch.setattr(httpx, "post", fake_post)
    try:
        from app.services.telegram import send_message

        result = send_message("hello")

        assert result is False
        assert calls == []
    finally:
        get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Test 2: formatter tests
# ---------------------------------------------------------------------------


def test_format_lead_message_escapes_and_includes_fields():
    from app.services.telegram import format_lead_message

    lead = LeadIn(
        name="Tom & Jerry <Co>",
        email="tom@example.com",
        phone="+15551234567",
        message="Need a quote for A < B",
        source="landing",
    )
    ai = AIResult(category="hot", summary="Wants a quote", reason="Buying intent")

    msg = format_lead_message(lead, ai)

    # special chars escaped (order: & first, then <, >)
    assert "Tom &amp; Jerry &lt;Co&gt;" in msg
    assert "A &lt; B" in msg
    # raw unescaped angle brackets from dynamic values must not leak
    assert "<Co>" not in msg
    # fields present
    assert "<b>Name:</b>" in msg
    assert "tom@example.com" in msg
    assert "+15551234567" in msg
    assert "<b>Category:</b> hot" in msg
    assert "<b>Summary:</b> Wants a quote" in msg
    # static formatting tags are intact
    assert "🔔 <b>New lead</b>" in msg
    # reason is not shown in the alert
    assert "Buying intent" not in msg


def test_format_lead_message_omits_absent_fields_and_ai():
    from app.services.telegram import format_lead_message

    lead = LeadIn(name="Solo", phone="+15550000000")
    msg = format_lead_message(lead, None)

    assert "<b>Name:</b> Solo" in msg
    assert "<b>Phone:</b>" in msg
    # absent optional fields are omitted
    assert "<b>Email:</b>" not in msg
    assert "<b>Message:</b>" not in msg
    assert "<b>Source:</b>" not in msg
    # ai is None -> no category / summary lines at all
    assert "<b>Category:</b>" not in msg
    assert "<b>Summary:</b>" not in msg


def test_format_lead_message_unknown_category_is_shown():
    from app.services.telegram import format_lead_message

    lead = LeadIn(name="Maybe Lead", email="maybe@example.com")
    ai = AIResult(category="unknown", summary=None, reason=None)

    msg = format_lead_message(lead, ai)
    # ai present but content was invalid -> category "unknown" IS shown (distinct from ai is None)
    assert "<b>Category:</b> unknown" in msg
    # no summary line when summary is None
    assert "<b>Summary:</b>" not in msg


# ---------------------------------------------------------------------------
# Test 3: resilience tests
# ---------------------------------------------------------------------------


def test_send_message_swallows_http_error(monkeypatch):
    monkeypatch.setenv("TELEGRAM_ENABLED", "true")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    get_settings.cache_clear()

    class _BadResponse:
        status_code = 400

        def raise_for_status(self) -> None:
            raise httpx.HTTPStatusError(
                "bad request",
                request=httpx.Request("POST", "https://api.telegram.org"),
                response=httpx.Response(400),
            )

    def fake_post(url: str, json: dict, timeout: float) -> _BadResponse:
        return _BadResponse()

    monkeypatch.setattr(httpx, "post", fake_post)
    try:
        from app.services.telegram import send_message

        result = send_message("hello")
        # error is swallowed -> False, no exception raised
        assert result is False
    finally:
        get_settings.cache_clear()


def test_send_message_swallows_network_error(monkeypatch):
    monkeypatch.setenv("TELEGRAM_ENABLED", "true")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    get_settings.cache_clear()

    def fake_post(url: str, json: dict, timeout: float) -> None:
        raise httpx.ConnectError("no network")

    monkeypatch.setattr(httpx, "post", fake_post)
    try:
        from app.services.telegram import send_message

        result = send_message("hello")
        assert result is False
    finally:
        get_settings.cache_clear()


