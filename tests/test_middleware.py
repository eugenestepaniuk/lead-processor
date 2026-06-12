"""Tests for BodySizeLimitMiddleware and SecurityHeadersMiddleware."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, raise_server_exceptions=False)


def test_body_too_large_returns_413() -> None:
    """A POST whose Content-Length exceeds 1 MB must be rejected with 413."""
    oversized_body = b"x" * (1 * 1024 * 1024 + 1)
    resp = client.post(
        "/api/leads",
        content=oversized_body,
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 413
    assert resp.json() == {"detail": "Request body too large"}


def test_security_headers_on_health() -> None:
    """GET /health must include the required security response headers."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers.get("x-content-type-options") == "nosniff"
    assert resp.headers.get("x-frame-options") == "DENY"

