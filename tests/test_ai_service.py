"""Tests for app/services/ai.py — Block 3, subtasks 3.1 & 3.3.

The conftest.py fixture sets AI_ENABLED=false before any app module is
imported, so all tests here run fully offline with no GEMINI_API_KEY required.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest

from app.schemas.lead import LeadIn
from app.services import ai
from app.services.ai import generate_summary


@pytest.fixture()
def sample_lead() -> LeadIn:
    return LeadIn(name="Test User", email="test@example.com")


# ---------------------------------------------------------------------------
# Test 1 (required): disabled path returns None without raising
# ---------------------------------------------------------------------------

def test_generate_summary_disabled_returns_none(sample_lead: LeadIn) -> None:
    """When AI_ENABLED=false, generate_summary must return None and not raise."""
    result = generate_summary(sample_lead)
    assert result is None


# ---------------------------------------------------------------------------
# Test 2 (recommended): disabled path makes NO network / client call
# ---------------------------------------------------------------------------

def test_generate_summary_disabled_makes_no_client_call(
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

    result = generate_summary(sample_lead)
    assert result is None


# ---------------------------------------------------------------------------
# Test 3 (3.3): AI enabled but Gemini call raises -> None + WARNING log
# ---------------------------------------------------------------------------

def test_generate_summary_api_failure_returns_none_and_logs_warning(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When AI is enabled but the API call raises, generate_summary must return
    None, must not propagate the exception, and must emit a WARNING log."""

    # Stub settings so AI appears enabled without real config validation.
    fake_settings = SimpleNamespace(
        ai_enabled=True,
        ai_model="gemini-2.5-flash",
        gemini_api_key="fake",
    )
    monkeypatch.setattr(ai, "get_settings", lambda: fake_settings)

    # Force the Gemini call to raise.
    def _boom(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("simulated AI failure")

    fake_client = SimpleNamespace(
        models=SimpleNamespace(generate_content=_boom)
    )
    monkeypatch.setattr(ai, "_get_client", lambda: fake_client)

    lead = LeadIn(name="Test User", email="test@example.com")

    with caplog.at_level(logging.WARNING):
        result = ai.generate_summary(lead)

    assert result is None
    assert any(rec.levelno == logging.WARNING for rec in caplog.records)


