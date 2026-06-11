"""Tests for app/services/ai.py — Block 3 (subtasks 3.1 & 3.3) + Block 4 (subtasks 4.2 & 4.3).

The conftest.py fixture sets AI_ENABLED=false before any app module is
imported, so all tests here run fully offline with no GEMINI_API_KEY required.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest

from app.schemas.ai_result import AIResult
from app.schemas.lead import LeadIn
from app.services import ai
from app.services.ai import analyze_lead


@pytest.fixture()
def sample_lead() -> LeadIn:
    return LeadIn(name="Test User", email="test@example.com")


# ---------------------------------------------------------------------------
# Test 1: disabled path returns None without raising
# ---------------------------------------------------------------------------

def test_analyze_lead_disabled_returns_none(sample_lead: LeadIn) -> None:
    """When AI_ENABLED=false, analyze_lead must return None and not raise."""
    result = analyze_lead(sample_lead)
    assert result is None


# ---------------------------------------------------------------------------
# Test 2: disabled path makes NO network / client call
# ---------------------------------------------------------------------------

def test_analyze_lead_disabled_makes_no_client_call(
    monkeypatch: pytest.MonkeyPatch,
    sample_lead: LeadIn,
) -> None:
    """Patch genai.Client so it raises if instantiated; still must return None."""

    def _boom(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("genai.Client must NOT be called when AI is disabled")

    import app.services.ai as ai_module

    monkeypatch.setattr(ai_module.genai, "Client", _boom)
    # Also clear the lru_cache so a previously cached client isn't reused.
    ai_module._get_client.cache_clear()

    result = analyze_lead(sample_lead)
    assert result is None


# ---------------------------------------------------------------------------
# Test 3: AI enabled but Gemini call raises -> None + WARNING log
# ---------------------------------------------------------------------------

def test_analyze_lead_api_failure_returns_none_and_logs_warning(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When AI is enabled but the API call raises, analyze_lead must return
    None, must not propagate the exception, and must emit a WARNING log."""

    fake_settings = SimpleNamespace(
        ai_enabled=True,
        ai_model="gemini-2.5-flash",
        gemini_api_key="fake",
    )
    monkeypatch.setattr(ai, "get_settings", lambda: fake_settings)

    def _boom(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("simulated AI failure")

    fake_client = SimpleNamespace(
        models=SimpleNamespace(generate_content=_boom)
    )
    monkeypatch.setattr(ai, "_get_client", lambda: fake_client)

    lead = LeadIn(name="Test User", email="test@example.com")

    with caplog.at_level(logging.WARNING):
        result = ai.analyze_lead(lead)

    assert result is None
    assert any(rec.levelno == logging.WARNING for rec in caplog.records)


# ---------------------------------------------------------------------------
# Test 4 (4.2): happy-path — valid JSON response parses into AIResult
# ---------------------------------------------------------------------------

def test_analyze_lead_happy_path_returns_ai_result(
    monkeypatch: pytest.MonkeyPatch,
    sample_lead: LeadIn,
) -> None:
    """With AI enabled and a well-formed JSON response, analyze_lead must return
    an AIResult with the correct category and summary.  No real network."""

    import app.services.ai as ai_module

    fake_settings = SimpleNamespace(
        ai_enabled=True,
        ai_model="gemini-2.5-flash",
        gemini_api_key="fake",
    )
    monkeypatch.setattr(ai_module, "get_settings", lambda: fake_settings)

    # Clear the cache before replacing _get_client with a plain lambda.
    ai_module._get_client.cache_clear()

    # Fake response whose .text is valid JSON for AIResult.
    fake_response = SimpleNamespace(
        text='{"summary":"hi","category":"hot","reason":"asked for a demo"}'
    )
    fake_client = SimpleNamespace(
        models=SimpleNamespace(generate_content=lambda **kw: fake_response)
    )
    monkeypatch.setattr(ai_module, "_get_client", lambda: fake_client)

    result = ai_module.analyze_lead(sample_lead)

    assert isinstance(result, AIResult)
    assert result.category == "hot"
    assert result.summary == "hi"


# ---------------------------------------------------------------------------
# Tests 5-7 (4.3): invalid model responses fall back to category="unknown"
# ---------------------------------------------------------------------------

def _make_fake_env(
    monkeypatch: pytest.MonkeyPatch,
    response_text: str,
) -> None:
    """Shared helper: patch get_settings + _get_client for fallback tests."""
    import app.services.ai as ai_module

    fake_settings = SimpleNamespace(
        ai_enabled=True,
        ai_model="gemini-2.5-flash",
        gemini_api_key="fake",
    )
    monkeypatch.setattr(ai_module, "get_settings", lambda: fake_settings)

    ai_module._get_client.cache_clear()

    fake_response = SimpleNamespace(text=response_text)
    fake_client = SimpleNamespace(
        models=SimpleNamespace(generate_content=lambda **kw: fake_response)
    )
    monkeypatch.setattr(ai_module, "_get_client", lambda: fake_client)


def test_analyze_lead_invalid_category_falls_back_to_unknown(
    monkeypatch: pytest.MonkeyPatch,
    sample_lead: LeadIn,
) -> None:
    """A category value outside the Literal (e.g. 'banana') must yield category='unknown'."""
    _make_fake_env(monkeypatch, '{"summary":"s","category":"banana","reason":"r"}')

    import app.services.ai as ai_module

    result = ai_module.analyze_lead(sample_lead)

    assert isinstance(result, AIResult)
    assert result.category == "unknown"


def test_analyze_lead_malformed_json_falls_back_to_unknown(
    monkeypatch: pytest.MonkeyPatch,
    sample_lead: LeadIn,
) -> None:
    """Completely non-JSON text must yield category='unknown', not None, not an exception."""
    _make_fake_env(monkeypatch, "not json at all")

    import app.services.ai as ai_module

    result = ai_module.analyze_lead(sample_lead)

    assert isinstance(result, AIResult)
    assert result.category == "unknown"


def test_analyze_lead_missing_category_falls_back_to_unknown(
    monkeypatch: pytest.MonkeyPatch,
    sample_lead: LeadIn,
) -> None:
    """JSON that omits the required 'category' key must yield category='unknown'."""
    _make_fake_env(monkeypatch, '{"summary":"s","reason":"r"}')

    import app.services.ai as ai_module

    result = ai_module.analyze_lead(sample_lead)

    assert isinstance(result, AIResult)
    assert result.category == "unknown"

