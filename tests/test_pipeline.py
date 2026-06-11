from __future__ import annotations

import pytest

from app.pipeline.process_lead import process_lead
from app.schemas.ai_result import AIResult
from app.schemas.lead import LeadIn


def test_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    lead_alice = LeadIn(name="Alice", email="alice@example.com")
    ai_result = AIResult(category="hot", summary="Short summary", reason="Budget ready")

    def fake_normalize(lead: LeadIn) -> LeadIn:
        calls.append("normalize")
        return lead

    def fake_analyze(lead: LeadIn) -> AIResult | None:
        calls.append("analyze")
        return ai_result

    def fake_save(lead: LeadIn, ai: AIResult | None) -> int:
        calls.append("save")
        return 42

    def fake_format(lead: LeadIn, ai: AIResult | None) -> str:
        calls.append("format")
        return "message"

    def fake_send(text: str) -> bool:
        calls.append("send")
        return True

    import app.pipeline.process_lead as mod
    monkeypatch.setattr(mod, "normalize_lead", fake_normalize)
    monkeypatch.setattr(mod, "analyze_lead", fake_analyze)
    monkeypatch.setattr(mod, "save_lead", fake_save)
    monkeypatch.setattr(mod, "format_lead_message", fake_format)
    monkeypatch.setattr(mod, "send_message", fake_send)

    result = process_lead(lead_alice)

    assert calls == ["normalize", "analyze", "save", "format", "send"]
    assert result.lead_id == 42
    assert result.summary == "Short summary"
    assert result.category == "hot"
    assert result.ai_ran is True
    assert result.notified is True


def test_ai_silent_notify_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    lead_bob = LeadIn(name="Bob", phone="+123456789")

    def fake_normalize(lead: LeadIn) -> LeadIn:
        calls.append("normalize")
        return lead

    def fake_analyze(lead: LeadIn) -> AIResult | None:
        calls.append("analyze")
        return None

    def fake_save(lead: LeadIn, ai: AIResult | None) -> int:
        calls.append("save")
        assert ai is None
        return 7

    def fake_format(lead: LeadIn, ai: AIResult | None) -> str:
        calls.append("format")
        return "message"

    def fake_send(text: str) -> bool:
        calls.append("send")
        return False

    import app.pipeline.process_lead as mod
    monkeypatch.setattr(mod, "normalize_lead", fake_normalize)
    monkeypatch.setattr(mod, "analyze_lead", fake_analyze)
    monkeypatch.setattr(mod, "save_lead", fake_save)
    monkeypatch.setattr(mod, "format_lead_message", fake_format)
    monkeypatch.setattr(mod, "send_message", fake_send)

    result = process_lead(lead_bob)

    assert calls == ["normalize", "analyze", "save", "format", "send"]
    assert result.summary is None
    assert result.category is None
    assert result.ai_ran is False
    assert result.notified is False


def test_storage_failure_propagates(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    lead = LeadIn(name="Carol", email="carol@example.com")

    import app.pipeline.process_lead as mod
    monkeypatch.setattr(mod, "normalize_lead", lambda ld: (calls.append("normalize") or ld))
    monkeypatch.setattr(mod, "analyze_lead", lambda ld: (calls.append("analyze") or None))

    def fake_save(lead: LeadIn, ai: AIResult | None) -> int:
        calls.append("save")
        raise RuntimeError("db down")

    monkeypatch.setattr(mod, "save_lead", fake_save)
    monkeypatch.setattr(mod, "format_lead_message", lambda ld, a: (calls.append("format") or ""))
    monkeypatch.setattr(mod, "send_message", lambda t: (calls.append("send") or True))

    with pytest.raises(RuntimeError, match="db down"):
        process_lead(lead)

    assert "send" not in calls
    assert "format" not in calls


def test_ai_unknown_still_persisted_and_notified(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    lead = LeadIn(name="Dave", phone="+19998887777")
    ai_unknown = AIResult(category="unknown", summary=None, reason=None)

    import app.pipeline.process_lead as mod
    monkeypatch.setattr(mod, "normalize_lead", lambda ld: (calls.append("normalize") or ld))
    monkeypatch.setattr(mod, "analyze_lead", lambda ld: (calls.append("analyze") or ai_unknown))
    monkeypatch.setattr(mod, "save_lead", lambda ld, a: (calls.append("save") or 99))
    monkeypatch.setattr(mod, "format_lead_message", lambda ld, a: (calls.append("format") or "msg"))
    monkeypatch.setattr(mod, "send_message", lambda t: (calls.append("send") or True))

    result = process_lead(lead)

    assert result.ai_ran is True
    assert result.category == "unknown"
    assert result.summary is None
    assert result.lead_id == 99
    assert result.notified is True
