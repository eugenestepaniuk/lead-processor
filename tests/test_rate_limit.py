"""Tests for per-IP rate limiting on POST /api/leads."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.pipeline.process_lead import ProcessResult


def _make_stub_result() -> ProcessResult:
    return ProcessResult(lead_id=1, summary="S", category="warm", ai_ran=False, notified=False)


@pytest.fixture()
def rate_limited_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Fresh app instance with the limiter storage cleared and process_lead stubbed."""
    # Import here so the fixture creates a clean slate each time.
    from app.rate_limit import limiter

    # Reset in-memory storage so prior test runs don't bleed through.
    limiter._storage.reset()  # type: ignore[attr-defined]

    import app.routes.leads as leads_mod

    monkeypatch.setattr(leads_mod, "process_lead", lambda payload: _make_stub_result())

    from app.main import app

    # Use raise_server_exceptions=False so 429 responses are returned as-is.
    return TestClient(app, raise_server_exceptions=False)


def test_sixth_request_is_rate_limited(rate_limited_client: TestClient) -> None:
    """The 6th POST within a minute from the same IP must return 429."""
    payload = {"name": "Jane Doe", "email": "jane@example.com"}

    for i in range(5):
        resp = rate_limited_client.post("/api/leads", json=payload)
        assert resp.status_code == 200, f"Request {i + 1} should succeed, got {resp.status_code}"

    resp = rate_limited_client.post("/api/leads", json=payload)
    assert resp.status_code == 429, f"6th request should be rate-limited, got {resp.status_code}"

